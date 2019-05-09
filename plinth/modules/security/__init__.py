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
from plinth import app as app_module
from plinth import menu

from .manifest import backup

version = 6

is_essential = True

name = _('Security')

managed_packages = ['fail2ban']

managed_services = ['fail2ban']

manual_page = 'Security'

ACCESS_CONF_FILE = '/etc/security/access.d/50freedombox.conf'
ACCESS_CONF_FILE_OLD = '/etc/security/access.conf'
ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx plinth (admin) (sudo):ALL'
OLD_ACCESS_CONF_SNIPPET = '-:ALL EXCEPT root fbx (admin) (sudo):ALL'
ACCESS_CONF_SNIPPETS = [OLD_ACCESS_CONF_SNIPPET, ACCESS_CONF_SNIPPET]

app = None


class SecurityApp(app_module.App):
    """FreedomBox app for security."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-security', name, None, 'fa-lock',
                              'security:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the module"""
    global app
    app = SecurityApp()
    app.set_enabled(True)


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    setup_fail2ban()

    # Migrate to new config file.
    enabled = get_restricted_access_enabled()
    set_restricted_access(False)
    if enabled:
        set_restricted_access(True)


def setup_fail2ban():
    actions.superuser_run('service', ['unmask', 'fail2ban'])
    actions.superuser_run('service', ['enable', 'fail2ban'])
    actions.superuser_run('service', ['reload', 'fail2ban'])


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
