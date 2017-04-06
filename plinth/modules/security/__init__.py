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
Plinth module for security configuration
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu


version = 1

is_essential = True

title = _('Security')


ACCESS_CONF_FILE = '/etc/security/access.conf'
ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx (admin) (sudo):ALL'


def init():
    """Initialize the module"""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-lock', 'security:index')


def get_restricted_access_enabled():
    """Return whether restricted access is enabled"""
    with open(ACCESS_CONF_FILE, 'r') as conffile:
        lines = conffile.readlines()

    for line in lines:
        if ACCESS_CONF_SNIPPET in line:
            return True

    return False


def set_restricted_access(enabled):
    """Enable or disable restricted access"""
    action = 'disable-restricted-access'
    if enabled:
        action = 'enable-restricted-access'

    actions.superuser_run('security', [action])
