# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for security configuration.
"""

import re
import subprocess
from collections import defaultdict

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu, module_loader
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages

from . import manifest

version = 7

is_essential = True

managed_packages = ['fail2ban', 'debsecan']

managed_services = ['fail2ban']

ACCESS_CONF_FILE = '/etc/security/access.d/50freedombox.conf'
ACCESS_CONF_FILE_OLD = '/etc/security/access.conf'
ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx plinth (admin) (sudo):ALL'
OLD_ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx (admin) (sudo):ALL'
ACCESS_CONF_SNIPPETS = [OLD_ACCESS_CONF_SNIPPET, ACCESS_CONF_SNIPPET]

app = None


class SecurityApp(app_module.App):
    """FreedomBox app for security."""

    app_id = 'security'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, name=_('Security'),
                               icon='fa-lock', manual_page='Security')
        self.add(info)

        menu_item = menu.Menu('menu-security', info.name, None, info.icon,
                              'security:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-security', managed_packages)
        self.add(packages)

        backup_restore = BackupRestore('backup-restore-security',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    if not old_version:
        enable_fail2ban()

    actions.superuser_run('service', ['reload', 'fail2ban'])

    # Migrate to new config file.
    enabled = get_restricted_access_enabled()
    set_restricted_access(False)
    if enabled:
        set_restricted_access(True)


def enable_fail2ban():
    actions.superuser_run('service', ['unmask', 'fail2ban'])
    actions.superuser_run('service', ['enable', 'fail2ban'])


def get_restricted_access_enabled():
    """Return whether restricted access is enabled"""
    with open(ACCESS_CONF_FILE_OLD, 'r') as conffile:
        if any(line.strip() in ACCESS_CONF_SNIPPETS
               for line in conffile.readlines()):
            return True

    try:
        with open(ACCESS_CONF_FILE, 'r') as conffile:
            return any(line.strip() in ACCESS_CONF_SNIPPETS
                       for line in conffile.readlines())
    except FileNotFoundError:
        return False


def set_restricted_access(enabled):
    """Enable or disable restricted access"""
    action = 'disable-restricted-access'
    if enabled:
        action = 'enable-restricted-access'

    actions.superuser_run('security', [action])


def get_apps_report():
    """Return a security report for each app"""
    lines = subprocess.check_output(['debsecan']).decode().split('\n')
    cves = defaultdict(set)
    for line in lines:
        if line:
            (label, package, *_) = line.split()
            cves[label].add(package)

    service_exposure_lines = subprocess.check_output(
        ['systemd-analyze', 'security']).decode().strip().split('\n')
    service_exposure_lines.pop(0)
    sandbox_coverage = {}
    for line in service_exposure_lines:
        fields = line.split()
        name = re.sub(r'\.service$', '', fields[0])
        score = round(100 - float(fields[1]) * 10)
        sandbox_coverage[name] = score

    apps = {
        'freedombox': {
            'name': 'freedombox',
            'packages': {'freedombox'},
            'vulns': 0,
        }
    }
    for module_name, module in module_loader.loaded_modules.items():
        try:
            packages = module.managed_packages
        except AttributeError:
            continue  # app has no managed packages

        try:
            services = module.managed_services
        except AttributeError:
            services = None

        # filter out apps not setup yet
        if module.setup_helper.get_state() == 'needs-setup':
            continue

        apps[module_name] = {
            'name': module_name,
            'packages': set(packages),
            'vulns': 0,
            'sandboxed': None,
        }

        if services:
            apps[module_name]['sandboxed'] = False
            for service in services:
                # If an app lists a timer, work on the associated service
                # instead
                if service.rpartition('.')[-1] == 'timer':
                    service = service.rpartition('.')[0]

                if _get_service_is_sandboxed(service):
                    apps[module_name]['sandboxed'] = True
                    apps[module_name][
                        'sandbox_coverage'] = sandbox_coverage.get(service)

    for cve_packages in cves.values():
        for app_ in apps.values():
            if cve_packages & app_['packages']:
                app_['vulns'] += 1

    return apps


def _get_service_is_sandboxed(service):
    """Return whether service is sandboxed."""
    lines = subprocess.check_output([
        'systemctl',
        'show',
        service,
        '--property=ProtectSystem',
        '--property=ProtectHome',
        '--property=PrivateTmp',
        '--property=PrivateDevices',
        '--property=PrivateNetwork',
        '--property=PrivateUsers',
        '--property=PrivateMounts',
    ]).decode().strip().split('\n')
    pairs = [line.partition('=')[::2] for line in lines]
    properties = dict(pairs)
    if properties.get('ProtectSystem') in ['yes', 'full', 'strict']:
        return True

    if properties.get('ProtectHome') in ['yes', 'read-only', 'tmpfs']:
        return True

    for name in [
            'PrivateTmp', 'PrivateDevices', 'PrivateNetwork', 'PrivateUsers',
            'PrivateMounts'
    ]:
        if properties.get(name) == 'yes':
            return True

    return False
