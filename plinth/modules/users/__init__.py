# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to manage users.
"""

import grp
import subprocess

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.package import Packages

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

    _version = 4

    can_be_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Users and Groups'),
                               icon='fa-users', description=_description,
                               manual_page='Users')
        self.add(info)

        menu_item = menu.Menu('menu-users', info.name, None, info.icon,
                              'users:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-users', [
            'ldapscripts', 'ldap-utils', 'libnss-ldapd', 'libpam-ldapd',
            'nscd', 'nslcd', 'samba-common-bin', 'slapd', 'tdb-tools'
        ])
        self.add(packages)

        daemon = Daemon('daemon-users', 'slapd', listen_ports=[(389, 'tcp4'),
                                                               (389, 'tcp6')])
        self.add(daemon)

        # Add the admin group
        groups = {'admin': _('Access to all services and system settings')}
        users_and_groups = UsersAndGroups('users-and-groups-admin',
                                          groups=groups)
        self.add(users_and_groups)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()

        results.append(_diagnose_ldap_entry('dc=thisbox'))
        results.append(_diagnose_ldap_entry('ou=people'))
        results.append(_diagnose_ldap_entry('ou=groups'))

        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            actions.superuser_run('users', ['first-setup'])

        actions.superuser_run('users', ['setup'])
        create_group('freedombox-share')


def _diagnose_ldap_entry(search_item):
    """Diagnose that an LDAP entry exists."""
    result = 'failed'

    try:
        subprocess.check_output(
            ['ldapsearch', '-x', '-b', 'dc=thisbox', search_item])
        result = 'passed'
    except subprocess.CalledProcessError:
        pass

    template = _('Check LDAP entry "{search_item}"')
    testname = format_lazy(template, search_item=search_item)

    return [testname, result]


def create_group(group):
    """Add an LDAP group."""
    actions.superuser_run('users', options=['create-group', group])


def remove_group(group):
    """Remove an LDAP group."""
    actions.superuser_run('users', options=['remove-group', group])


def get_last_admin_user():
    """If there is only one admin user return its name else return None."""
    output = actions.superuser_run('users', ['get-group-users', 'admin'])
    admin_users = output.strip().split('\n')

    if len(admin_users) == 1 and admin_users[0]:
        return admin_users[0]

    return None


def add_user_to_share_group(username, service=None):
    """Add user to the freedombox-share group."""
    try:
        group_members = grp.getgrnam('freedombox-share').gr_mem
    except KeyError:
        group_members = []
    if username not in group_members:
        actions.superuser_run(
            'users', ['add-user-to-group', username, 'freedombox-share'])
        if service:
            actions.superuser_run('service', ['try-restart', service])
