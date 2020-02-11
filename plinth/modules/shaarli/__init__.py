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
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from .manifest import clients

version = 1

managed_packages = ['shaarli']

_description = [
    _('Shaarli allows you to save and share bookmarks.'),
    _('When enabled, Shaarli will be available from <a href="/shaarli" '
      'data-turbolinks="false">/shaarli</a> path on the web server. Note that '
      'Shaarli only supports a single user account, which you will need to '
      'setup on the initial visit.'),
]

app = None


class ShaarliApp(app_module.App):
    """FreedomBox app for Shaarli."""

    app_id = 'shaarli'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Shaarli'), icon_filename='shaarli',
                               short_description=_('Bookmarks'),
                               description=_description, manual_page='Shaarli',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-shaarli', info.name,
                              info.short_description, info.icon_filename,
                              'shaarli:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-shaarli', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/shaarli',
                                      clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-shaarli', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-shaarli', 'shaarli')
        self.add(webserver)


def init():
    """Initialize the module."""
    global app
    app = ShaarliApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
