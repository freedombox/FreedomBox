#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app to manage users.
"""

import subprocess

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth.menu import main_menu

version = 2

is_essential = True

managed_packages = [
    'ldapscripts', 'ldap-utils', 'libnss-ldapd', 'libpam-ldapd', 'nslcd',
    'slapd'
]

first_boot_steps = [
    {
        'id': 'users_firstboot',
        'url': 'users:firstboot',
        'order': 1
    },
]

name = _('Users and Groups')

# All FreedomBox user groups
groups = dict()


def init():
    """Intialize the user module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-user', 'users:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    if not old_version:
        helper.call('post', actions.superuser_run, 'users', ['first-setup'])
    helper.call('post', actions.superuser_run, 'users', ['setup'])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(389, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(389, 'tcp6'))

    results.append(_diagnose_ldap_entry('dc=thisbox'))
    results.append(_diagnose_ldap_entry('ou=people'))
    results.append(_diagnose_ldap_entry('ou=groups'))

    return results


def _diagnose_ldap_entry(search_item):
    """Diagnose that an LDAP entry exists."""
    result = 'failed'

    try:
        subprocess.check_output(
            ['ldapsearch', '-x', '-b', 'dc=thisbox', search_item])
        result = 'passed'
    except subprocess.CalledProcessError:
        pass

    return [
        _('Check LDAP entry "{search_item}"').format(search_item=search_item),
        result
    ]


def create_group(group):
    """Add an LDAP group."""
    actions.superuser_run('users', options=['create-group', group])


def remove_group(group):
    """Remove an LDAP group."""
    actions.superuser_run('users', options=['remove-group', group])


def register_group(group):
    groups[group[0]] = group[1]


def get_last_admin_user():
    """ Check if there is only one admin user
        if yes return its name else return None
    """
    admin_users = actions.superuser_run(
        'users', ['get-group-users', 'admin']).strip().split('\n')
    if len(admin_users) == 1:
        return admin_users[0]
    return None
