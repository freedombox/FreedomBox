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

import json

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import clients  # noqa, pylint: disable=unused-import


version = 1

managed_packages = ['wireguard']

name = _('WireGuard')

short_description = _('Virtual Private Network')

description = [
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

clients = clients

port_forwarding_info = [('UDP', 51820)]

app = None

SERVER_INTERFACE = 'wg0'


class WireguardApp(app_module.App):
    """FreedomBox app for wireguard."""

    app_id = 'wireguard'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-wireguard', name, short_description,
                              'wireguard', 'wireguard:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-wireguard', name, short_description=short_description,
            icon='wireguard', description=description,
            configure_url=reverse_lazy('wireguard:index'), login_required=True,
            clients=clients)
        self.add(shortcut)

        firewall = Firewall('firewall-wireguard', name,
                            ports=['wireguard-freedombox'], is_external=True)
        self.add(firewall)


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
    helper.call('post', actions.superuser_run, 'wireguard', ['setup'])
    helper.call('post', app.enable)


def get_public_key():
    """Return this box's public key."""
    public_key_path = '/var/lib/freedombox/wireguard/publickey'
    try:
        with open(public_key_path) as public_key_file:
            public_key = public_key_file.read().strip()

    except FileNotFoundError:
        public_key = None

    return public_key


def get_info():
    """Return server and clients info."""
    output = actions.superuser_run('wireguard', ['get-info'])
    info = json.loads(output)
    my_server_info = info.pop(SERVER_INTERFACE)
    my_client_servers = []
    for interface in info.values():
        if interface['peers']:
            my_client_servers.append(interface['peers'][0])

    return {
        'my_server': {
            'public_key': my_server_info['public_key'],
            'clients': my_server_info['peers'],
        },
        'my_client': {
            'servers': my_client_servers,
        },
    }
