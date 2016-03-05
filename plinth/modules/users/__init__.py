#
# This file is part of Plinth.
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
Plinth module to manage users
"""

from django.utils.translation import ugettext_lazy as _
import subprocess

from plinth import cfg
from plinth import action_utils

version = 1

is_essential = True

depends = ['system']

title = _('Users and Groups')


def init():
    """Intialize the user module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(title, 'glyphicon-user', 'users:index', 15)


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
        subprocess.check_output(['ldapsearch', '-x', '-b', 'dc=thisbox',
                                 search_item])
        result = 'passed'
    except subprocess.CalledProcessError:
        pass

    return [_('Check LDAP entry "{search_item}"')
            .format(search_item=search_item), result]
