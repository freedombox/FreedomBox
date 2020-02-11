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
FreedomBox app for wireguard.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy, import_from_gi

from . import utils
from .manifest import clients  # noqa, pylint: disable=unused-import

nm = import_from_gi('NM', '1.0')

version = 1

managed_packages = ['wireguard']

_description = [
    _('WireGuard is a fast, modern, secure VPN tunnel.'),
    format_lazy(
        _('It can be used to connect to a VPN provider which supports '
          'WireGuard, and to route all outgoing traffic from {box_name} '
          'through the VPN.'), box_name=_(cfg.box_name)),
    format_lazy(
        _('A second use case is to connect a mobile device to {box_name} '
          'while travelling. While connected to a public Wi-Fi network, all '
          'traffic can be securely relayed through {box_name}.'),
        box_name=_(cfg.box_name))
]

port_forwarding_info = [('UDP', 51820)]

app = None

SERVER_INTERFACE = 'wg0'


class WireguardApp(app_module.App):
    """FreedomBox app for wireguard."""

    app_id = 'wireguard'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('WireGuard'), icon_filename='wireguard',
                               short_description=_('Virtual Private Network'),
                               description=_description, clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-wireguard', info.name,
                              info.short_description, info.icon_filename,
                              'wireguard:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-wireguard', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('wireguard:index'), login_required=True,
            clients=info.clients)
        self.add(shortcut)

        firewall = Firewall('firewall-wireguard', info.name,
                            ports=['wireguard-freedombox'], is_external=True)
        self.add(firewall)

    def enable(self):
        """Enable the app by simply storing a flag in key/value store."""
        from plinth import kvstore
        super().enable()
        kvstore.set('wireguard-enabled', True)
        utils.enable_connections(True)

    def disable(self):
        """Disable the app by simply storing a flag in key/value store."""
        from plinth import kvstore
        super().disable()
        kvstore.set('wireguard-enabled', False)
        utils.enable_connections(False)

    def is_enabled(self):
        """Return whether all leader components are enabled and flag is set."""
        from plinth import kvstore
        enabled = super().is_enabled()
        return enabled and kvstore.get_default('wireguard-enabled', False)


def init():
    """Initialize the module."""
    global app
    app = WireguardApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
