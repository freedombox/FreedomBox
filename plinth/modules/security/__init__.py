# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for security configuration."""

import re
import subprocess
from collections import defaultdict

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon, RelatedDaemon
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages
from plinth.privileged import service as service_privileged

from . import manifest, privileged


class SecurityApp(app_module.App):
    """FreedomBox app for security."""

    app_id = 'security'

    _version = 7

    can_be_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Security'),
                               icon='fa-lock', manual_page='Security')
        self.add(info)

        menu_item = menu.Menu('menu-security', info.name, None, info.icon,
                              'security:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-security', ['fail2ban', 'debsecan'])
        self.add(packages)

        daemon = RelatedDaemon('related-daemon-fail2ban', 'fail2ban')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-security',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            enable_fail2ban()

        service_privileged.reload('fail2ban')

        # Migrate to new config file.
        enabled = privileged.get_restricted_access_enabled()
        set_restricted_access(False)
        if enabled:
            set_restricted_access(True)


def enable_fail2ban():
    """Unmask, enable and run the fail2ban service."""
    service_privileged.unmask('fail2ban')
    service_privileged.enable('fail2ban')


def set_restricted_access(enabled):
    """Enable or disable restricted access."""
    if enabled:
        privileged.enable_restricted_access()
    else:
        privileged.disable_restricted_access()


def get_apps_report():
    """Return a security report for each app."""
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
    for app_ in app_module.App.list():
        components = app_.get_components_of_type(Packages)
        packages = []
        for component in components:
            packages += component.possible_packages

        if not packages:
            continue  # app has no managed packages

        components = app_.get_components_of_type(Daemon)
        services = []
        for component in components:
            services.append(component.unit)

        # filter out apps not setup yet
        if app_.needs_setup():
            continue

        apps[app_.app_id] = {
            'name': app_.app_id,
            'packages': set(packages),
            'vulns': 0,
            'sandboxed': None,
        }

        if services:
            apps[app_.app_id]['sandboxed'] = False
            for service in services:
                # If an app lists a timer, work on the associated service
                # instead
                if service.rpartition('.')[-1] == 'timer':
                    service = service.rpartition('.')[0]

                if _get_service_is_sandboxed(service):
                    apps[app_.app_id]['sandboxed'] = True
                    apps[app_.app_id][
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
