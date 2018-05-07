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
FreedomBox app for security configuration.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu

version = 3

is_essential = True

name = _('Security')

managed_packages = ['fail2ban']

managed_services = ['fail2ban']

manual_page = 'Security'

ACCESS_CONF_FILE = '/etc/security/access.conf'
ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx plinth (admin) (sudo):ALL'
OLD_ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx (admin) (sudo):ALL'
ACCESS_CONF_SNIPPETS = [OLD_ACCESS_CONF_SNIPPET, ACCESS_CONF_SNIPPET]


def init():
    """Initialize the module"""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-lock', 'security:index')


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    setup_fail2ban()


def setup_fail2ban():
    actions.superuser_run('service', ['unmask', 'fail2ban'])
    actions.superuser_run('service', ['enable', 'fail2ban'])


def get_restricted_access_enabled():
    """Return whether restricted access is enabled"""
    with open(ACCESS_CONF_FILE, 'r') as conffile:
        return any(line.strip() in ACCESS_CONF_SNIPPETS
                   for line in conffile.readlines())


def set_restricted_access(enabled):
    """Enable or disable restricted access"""
    action = 'disable-restricted-access'
    if enabled:
        action = 'enable-restricted-access'

    actions.superuser_run('security', [action])
