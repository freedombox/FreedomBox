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
FreedomBox app to configure Shadowsocks.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

name = _('Shadowsocks')

icon_filename = 'shadowsocks'

short_description = _('Socks5 Proxy')

managed_services = ['shadowsocks-libev-local@freedombox']

managed_packages = ['shadowsocks-libev']

description = [
    _('Shadowsocks is a lightweight and secure SOCKS5 proxy, designed to '
      'protect your Internet traffic. It can be used to bypass Internet '
      'filtering and censorship.'),
    format_lazy(
        _('Your {box_name} can run a Shadowsocks client, that can connect to '
          'a Shadowsocks server. It will also run a SOCKS5 proxy. Local '
          'devices can connect to this proxy, and their data will be '
          'encrypted and proxied through the Shadowsocks server.'),
        box_name=_(cfg.box_name)),
    _('To use Shadowsocks after setup, set the SOCKS5 proxy URL in your '
      'device, browser or application to http://freedombox_address:1080/')
]

manual_page = 'Shadowsocks'

app = None


class ShadowsocksApp(app_module.App):
    """FreedomBox app for Shadowsocks."""

    app_id = 'shadowsocks'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-shadowsocks', name, short_description,
                              'shadowsocks', 'shadowsocks:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-shadowsocks', name, short_description=short_description,
            icon=icon_filename, description=description,
            configure_url=reverse_lazy('shadowsocks:index'),
            login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-shadowsocks', name,
                            ports=['shadowsocks-local-plinth'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon('daemon-shadowsocks', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the module."""
    global app
    app = ShadowsocksApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'shadowsocks', ['setup'])
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(1080, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(1080, 'tcp6'))

    return results
