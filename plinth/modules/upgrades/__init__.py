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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app for upgrades.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu
from plinth import service as service_module

from .manifest import backup

version = 1

is_essential = True

managed_packages = ['unattended-upgrades']

name = _('Update')

description = [
    _('Check for and apply the latest software and security updates.')
]

service = None

manual_page = 'Upgrades'

app = None


class UpgradesApp(app_module.App):
    """FreedomBox app for software upgrades."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-upgrades', name, None, 'fa-refresh',
                              'upgrades:index', parent_url_name='system')
        self.add(menu_item)


def init():
    """Initialize the module."""
    global app
    app = UpgradesApp()
    app.set_enabled(True)

    global service
    service = service_module.Service('auto-upgrades', name,
                                     is_enabled=is_enabled, enable=enable,
                                     disable=disable)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'upgrades', ['enable-auto'])


def is_enabled():
    """Return whether the module is enabled."""
    output = actions.run('upgrades', ['check-auto'])
    return 'True' in output.split()


def enable():
    """Enable the module."""
    actions.superuser_run('upgrades', ['enable-auto'])


def disable():
    """Disable the module."""
    actions.superuser_run('upgrades', ['disable-auto'])
