# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to manage users."""

import grp
import subprocess

import augeas
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import cfg, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)
from plinth.package import Packages
from plinth.privileged import service as service_privileged

from . import privileged
from .components import UsersAndGroups

first_boot_steps = [
    {
        'id': 'users_firstboot',
        'url': 'users:firstboot',
        'order': 1
    },
]

_description = [
    _('Create and manage user accounts. These accounts serve as centralized '
      'authentication mechanism for most apps. Some apps further require a '
      'user account to be part of a group to authorize the user to access the '
      'app.'),
    format_lazy(
        _('Any user may login to {box_name} web interface to see a list of '
          'apps relevant to them in the home page. However, only users of '
          'the <em>admin</em> group may alter apps or system settings.'),
        box_name=_(cfg.box_name))
]


class UsersApp(app_module.App):
    """FreedomBox app for users and groups management."""

    app_id = 'users'

    _version = 7

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Users and Groups'),
                               icon='fa-users', description=_description,
                               manual_page='Users')
        self.add(info)

        menu_item = menu.Menu('menu-users', info.name, None, info.icon,
                              'users:index', parent_url_name='system:system',
                              order=10)
        self.add(menu_item)

        packages = Packages('packages-users', [
            'ldapscripts', 'ldap-utils', 'libnss-ldapd', 'libpam-ldapd',
            'nslcd', 'samba-common-bin', 'slapd', 'tdb-tools'
        ])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-users', [
            '/etc/apache2/includes/freedombox-auth-ldap.conf',
        ])
        self.add(dropin_configs)

        daemon = Daemon('daemon-users', 'slapd', listen_ports=[(389, 'tcp4'),
                                                               (389, 'tcp6')])
        self.add(daemon)

        # Add the admin group
        groups = {'admin': _('Access to all services and system settings')}
        users_and_groups = UsersAndGroups('users-and-groups-admin',
                                          groups=groups)
        self.add(users_and_groups)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()

        results.append(_diagnose_ldap_entry('dc=thisbox'))
        results.append(_diagnose_ldap_entry('ou=users'))
        results.append(_diagnose_ldap_entry('ou=groups'))
        results.append(_diagnose_ldap_entry('ou=policies'))
        results.append(_diagnose_ldap_entry('cn=DefaultPPolicy'))

        config = privileged.get_nslcd_config()
        results.append(_diagnose_nslcd_config(config, 'uri', 'ldapi:///'))
        results.append(_diagnose_nslcd_config(config, 'base', 'dc=thisbox'))
        results.append(_diagnose_nslcd_config(config, 'sasl_mech', 'EXTERNAL'))
        results.extend(_diagnose_nsswitch_config())

        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            privileged.first_setup()

        if old_version and old_version < 7:
            # Setup password policy and lock LDAP passwords for inactive users.
            inactivated_users = _get_inactivated_users()
            if inactivated_users:
                privileged.setup_and_sync_user_states(inactivated_users)

        privileged.setup()
        privileged.create_group('freedombox-share')


def _diagnose_ldap_entry(search_item: str) -> DiagnosticCheck:
    """Diagnose that an LDAP entry exists."""
    check_id = f'users-ldap-entry-{search_item}'
    result = Result.FAILED

    try:
        output = subprocess.check_output(
            ['ldapsearch', '-LLL', '-x', '-b', 'dc=thisbox', search_item])
        if search_item in output.decode():
            result = Result.PASSED
    except subprocess.CalledProcessError:
        pass

    description = gettext_noop('Check LDAP entry "{search_item}"')
    parameters: DiagnosticCheckParameters = {'search_item': search_item}

    return DiagnosticCheck(check_id, description, result, parameters)


def _diagnose_nslcd_config(config: dict[str, str], key: str,
                           value: str) -> DiagnosticCheck:
    """Diagnose that nslcd has a configuration."""
    check_id = f'users-nslcd-config-{key}'
    try:
        result = Result.PASSED if config[key] == value else Result.FAILED
    except KeyError:
        result = Result.FAILED

    description = gettext_noop('Check nslcd config "{key} {value}"')
    parameters: DiagnosticCheckParameters = {'key': key, 'value': value}

    return DiagnosticCheck(check_id, description, result, parameters)


def _diagnose_nsswitch_config() -> list[DiagnosticCheck]:
    """Diagnose that Name Service Switch is configured to use LDAP."""
    nsswitch_conf = '/etc/nsswitch.conf'
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Nsswitch', nsswitch_conf)
    aug.set('/augeas/context', '/files' + nsswitch_conf)
    aug.load()

    results = []
    for database in ['passwd', 'group', 'shadow']:
        check_id = f'users-nsswitch-config-{database}'
        result = Result.FAILED
        for match in aug.match('database'):
            if aug.get(match) != database:
                continue

            for service_match in aug.match(match + '/service'):
                if 'ldap' == aug.get(service_match):
                    result = Result.PASSED
                    break

            break

        description = gettext_noop('Check nsswitch config "{database}"')
        parameters: DiagnosticCheckParameters = {'database': database}

        results.append(
            DiagnosticCheck(check_id, description, result, parameters))

    return results


def get_last_admin_user():
    """If there is only one admin user return its name else return None."""
    admin_users = privileged.get_group_users('admin')
    if len(admin_users) == 1 and admin_users[0]:
        return admin_users[0]

    return None


def _get_inactivated_users() -> list[str]:
    """Get list of inactivated usernames"""
    from django.contrib.auth.models import User
    users = User.objects.filter(is_active=False)

    return [user.username for user in users]


def add_user_to_share_group(username, service=None):
    """Add user to the freedombox-share group."""
    try:
        group_members = grp.getgrnam('freedombox-share').gr_mem
    except KeyError:
        group_members = []
    if username not in group_members:
        privileged.add_user_to_group(username, 'freedombox-share')
        if service:
            service_privileged.try_restart(service)
