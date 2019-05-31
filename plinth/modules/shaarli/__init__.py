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
FreedomBox app to configure Shaarli.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth import service as service_module
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from .manifest import clients

version = 1

managed_packages = ['shaarli']

name = _('Shaarli')

short_description = _('Bookmarks')

description = [
    _('Shaarli allows you to save and share bookmarks.'),
    _('When enabled, Shaarli will be available from <a href="/shaarli">'
      '/shaarli</a> path on the web server. Note that Shaarli only supports a '
      'single user account, which you will need to setup on the initial '
      'visit.'),
]

clients = clients

service = None

manual_page = 'Shaarli'

app = None


class ShaarliApp(app_module.App):
    """FreedomBox app for Shaarli."""

    app_id = 'shaarli'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-shaarli', name, short_description,
                              'shaarli', 'shaarli:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-shaarli', name,
                                      short_description=short_description,
                                      icon='shaarli', url='/shaarli',
                                      clients=clients, login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-shaarli', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-shaarli', 'shaarli')
        self.add(webserver)


def init():
    """Initialize the module."""
    global app
    app = ShaarliApp()

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service('shaarli', name,
                                         is_enabled=is_enabled, enable=enable,
                                         disable=disable)

        if is_enabled():
            app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service('shaarli', name,
                                         is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    helper.call('post', app.enable)


def is_enabled():
    """Return whether the module is enabled."""
    return app.is_enabled()


def enable():
    """Enable the module."""
    app.enable()


def disable():
    """Enable the module."""
    app.disable()
