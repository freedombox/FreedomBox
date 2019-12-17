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
FreedomBox app for infinoted.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy
from plinth.views import AppView

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['infinoted']

managed_packages = ['infinoted']

manual_page = 'Infinoted'

name = _('infinoted')

icon_filename = 'infinoted'

short_description = _('Gobby Server')

description = [
    _('infinoted is a server for Gobby, a collaborative text editor.'),
    format_lazy(
        _('To use it, <a href="https://gobby.github.io/">download Gobby</a>, '
          'desktop client and install it. Then start Gobby and select '
          '"Connect to Server" and enter your {box_name}\'s domain name.'),
        box_name=_(cfg.box_name)),
]

clients = clients

port_forwarding_info = [('TCP', 6523)]

app = None


class InfinotedApp(app_module.App):
    """FreedomBox app for infinoted."""

    app_id = 'infinoted'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-infinoted', name, short_description,
                              'infinoted', 'infinoted:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-infinoted', name, short_description=short_description,
            icon=icon_filename, description=description,
            configure_url=reverse_lazy('infinoted:index'), clients=clients,
            login_required=False)
        self.add(shortcut)

        firewall = Firewall('firewall-infinoted', name,
                            ports=['infinoted-plinth'], is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-infinoted', managed_services[0],
                        listen_ports=[(6523, 'tcp4'), (6523, 'tcp6')])
        self.add(daemon)


def init():
    """Initialize the infinoted module."""
    global app
    app = InfinotedApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


class InfinotedAppView(AppView):
    app_id = 'infinoted'
    name = name
    description = description
    clients = clients
    port_forwarding_info = port_forwarding_info
    icon_filename = icon_filename


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'infinoted', ['setup'])
    helper.call('post', app.enable)
