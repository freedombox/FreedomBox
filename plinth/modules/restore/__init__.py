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
FreedomBox app to configure reStore.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth import service as service_module
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import clients

version = 1

managed_services = ['node-restore']

managed_packages = ['node-restore']

name = _('reStore')

short_description = _('Unhosted Storage')

description = [
    format_lazy(
        _('reStore is a server for <a href=\'https://unhosted.org/\'>'
          'unhosted</a> web applications.  The idea is to uncouple web '
          'applications from data.  No matter where a web application is '
          'served from, the data can be stored on an unhosted storage '
          'server of user\'s choice.  With reStore, your {box_name} becomes '
          'your unhosted storage server.'), box_name=_(cfg.box_name)),
    _('You can create and edit accounts in the '
      '<a href=\'/restore/\'>reStore web-interface</a>.')
]

clients = clients

reserved_usernames = ['node-restore']

service = None

app = None


class RestoreApp(app_module.App):
    """FreedomBox app for Restore."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-restore', name, short_description,
                              'fa-hdd-o', 'restore:index',
                              parent_url_name='apps')
        self.add(menu_item)

        firewall = Firewall('firewall-restore', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)


def init():
    """Initialize the reStore module."""
    global app
    app = RestoreApp()

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name)
