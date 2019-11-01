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

import datetime
import json

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy, import_from_gi

from .manifest import clients  # noqa, pylint: disable=unused-import

nm = import_from_gi('NM', '1.0')

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


def get_nm_info():
    """Get information from network manager."""
    client = nm.Client.new(None)

    connections = {}
    for connection in client.get_connections():
        if connection.get_connection_type() != 'wireguard':
            continue

        settings = connection.get_setting_by_name('wireguard')
        secrets = connection.get_secrets('wireguard')
        connection.update_secrets('wireguard', secrets)

        info = {}
        info['interface'] = connection.get_interface_name()
        info['private_key'] = settings.get_private_key()
        info['listen_port'] = settings.get_listen_port()
        info['fwmark'] = settings.get_fwmark()
        info['mtu'] = settings.get_mtu()
        info['default_route'] = settings.get_ip4_auto_default_route()
        info['peers'] = []
        for peer_index in range(settings.get_peers_len()):
            peer = settings.get_peer(peer_index)
            peer_info = {
                'endpoint': peer.get_endpoint(),
                'public_key': peer.get_public_key(),
                'preshared_key': peer.get_preshared_key(),
                'persistent_keepalive': peer.get_persistent_keepalive(),
                'allowed_ips': []
            }
            for index in range(peer.get_allowed_ips_len()):
                allowed_ip = peer.get_allowed_ip(index, None)
                peer_info['allowed_ips'].append(allowed_ip)

            info['peers'].append(peer_info)

        settings_ipv4 = connection.get_setting_ip4_config()
        if settings_ipv4 and settings_ipv4.get_num_addresses():
            info['ip_address'] = settings_ipv4.get_address(0).get_address()

        connections[info['interface']] = info

    return connections


def get_info():
    """Return server and clients info."""
    output = actions.superuser_run('wireguard', ['get-info'])
    status = json.loads(output)

    nm_info = get_nm_info()

    my_server_info = status.pop(SERVER_INTERFACE, {})
    my_client_servers = {}

    for interface, info in nm_info.items():
        my_client_servers[interface] = info

        if interface not in status:
            continue

        for info_peer in info['peers']:
            for status_peer in status[interface]['peers']:
                if info_peer['public_key'] == status_peer['public_key']:
                    info_peer['status'] = status_peer
                    status_peer['latest_handshake'] = \
                        datetime.datetime.fromtimestamp(
                            int(status_peer['latest_handshake']))

    return {
        'my_server': {
            'public_key': my_server_info.get('public_key'),
            'clients': my_server_info.get('peers'),
        },
        'my_client': {
            'servers': my_client_servers,
        },
    }
