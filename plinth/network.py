#
# This file is part of Plinth.
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
Helper functions for working with network manager.
"""

from dbus.exceptions import DBusException
from gettext import gettext as _
import NetworkManager
import uuid
import urllib


CONNECTION_TYPE_NAMES = {
    '802-3-ethernet': 'Ethernet',
    '802-11-wireless': 'Wi-Fi',
}


class ConnectionNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


class DeviceNotFound(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg


def get_connection_list():
    """Get a list of active and available connections."""
    connections = []
    active = []

    for conn in NetworkManager.NetworkManager.ActiveConnections:
        try:
            settings = conn.Connection.GetSettings()['connection']
        except DBusException:
            # DBusException can be thrown here if the connection list is loaded
            # quickly after a connection is deactivated.
            continue
        active.append(settings['id'])

    for conn in NetworkManager.Settings.ListConnections():
        settings = conn.GetSettings()['connection']
        # Display a friendly type name if known.
        conn_type = CONNECTION_TYPE_NAMES.get(settings['type'],
                                              settings['type'])
        connections.append({
            'name': settings['id'],
            'id': urllib.parse.quote_plus(settings['id']),
            'type': conn_type,
            'is_active': settings['id'] in active,
        })
    connections.sort(key=lambda x: x['is_active'], reverse=True)
    return connections


def get_connection(name):
    """Returns connection with id matching name.
    Returns None if not found.
    """
    connections = NetworkManager.Settings.ListConnections()
    connections = dict([(x.GetSettings()['connection']['id'], x)
                        for x in connections])
    return connections.get(name)


def get_active_connection(name):
    """Returns active connection with id matching name.
    Returns None if not found.
    """
    connections = NetworkManager.NetworkManager.ActiveConnections
    connections = dict([(x.Connection.GetSettings()['connection']['id'], x)
                        for x in connections])
    return connections.get(name)


def edit_ethernet_connection(conn, name, ipv4_method, ipv4_address):
    settings = conn.GetSettings()

    new_settings = {
        'connection': {
            'id': name,
            'type': settings['connection']['type'],
            'uuid': settings['connection']['uuid'],
        },
        '802-3-ethernet': {},
        'ipv4': {'method': ipv4_method},
    }
    if ipv4_method == 'manual' and ipv4_address:
        new_settings['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    conn.Update(new_settings)


def edit_wifi_connection(conn, name,
                         ssid, auth_mode, passphrase,
                         ipv4_method, ipv4_address):
    settings = conn.GetSettings()

    new_settings = {
        'connection': {
            'id': name,
            'type': settings['connection']['type'],
            'uuid': settings['connection']['uuid'],
        },
        '802-11-wireless': {
            'ssid': ssid,
        },
        'ipv4': {'method': ipv4_method},
    }

    if auth_mode == 'wpa' and passphrase:
        new_settings['connection']['security'] = '802-11-wireless-security'
        new_settings['802-11-wireless-security'] = {
            'key-mgmt': 'wpa-psk',
            'psk': passphrase,
        }

    if ipv4_method == 'manual' and ipv4_address:
        new_settings['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    conn.Update(new_settings)


def activate_connection(name):
    # Find the connection
    conn = get_connection(name)
    if not conn:
        raise ConnectionNotFound(
            _('Failed to activate connection %s: '
              'Connection not found.') % name)

    # Find a suitable device
    ctype = conn.GetSettings()['connection']['type']
    if ctype == 'vpn':
        for dev in NetworkManager.NetworkManager.GetDevices():
            if (dev.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED
                and dev.Managed):
                break
        else:
            raise DeviceNotFound(
                _('Failed to activate connection %s: '
                  'No suitable device is available.') % name)
    else:
        dtype = {
            '802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI,
            '802-3-ethernet': NetworkManager.NM_DEVICE_TYPE_ETHERNET,
            'gsm': NetworkManager.NM_DEVICE_TYPE_MODEM,
        }.get(ctype, ctype)

        for dev in NetworkManager.NetworkManager.GetDevices():
            if (dev.DeviceType == dtype
                and dev.State == NetworkManager.NM_DEVICE_STATE_DISCONNECTED):
                break
        else:
            raise DeviceNotFound(
                _('Failed to activate connection %s: '
                  'No suitable device is available.') % name)

    NetworkManager.NetworkManager.ActivateConnection(conn, dev, "/")


def deactivate_connection(name):
    active = get_active_connection(name)
    if active:
        NetworkManager.NetworkManager.DeactivateConnection(active)
    else:
        raise ConnectionNotFound(
            _('Failed to deactivate connection %s: '
              'Connection not found.') % name)


def add_ethernet_connection(name, ipv4_method, ipv4_address):
    conn = {
        'connection': {
            'id': name,
            'type': '802-3-ethernet',
            'uuid': str(uuid.uuid4()),
        },
        '802-3-ethernet': {},
        'ipv4': {'method': ipv4_method},
    }

    if ipv4_method == 'manual' and ipv4_address:
        conn['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    NetworkManager.Settings.AddConnection(conn)


def add_wifi_connection(name,
                        ssid, auth_mode, passphrase,
                        ipv4_method, ipv4_address):
    conn = {
        'connection': {
            'id': name,
            'type': '802-11-wireless',
            'uuid': str(uuid.uuid4()),
        },
        '802-11-wireless': {
            'ssid': ssid,
        },
        'ipv4': {'method': ipv4_method},
    }

    if auth_mode == 'wpa' and passphrase:
        conn['connection']['security'] = '802-11-wireless-security'
        conn['802-11-wireless-security'] = {
            'key-mgmt': 'wpa-psk',
            'psk': passphrase,
        }

    if ipv4_method == 'manual' and ipv4_address:
        conn['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    NetworkManager.Settings.AddConnection(conn)


def delete_connection(name):
    conn = get_connection(name)
    if not conn:
        raise ConnectionNotFound(
            _('Failed to delete connection %s: '
              'Connection not found.') % name)
    conn.Delete()


def wifi_scan():
    aps = []
    for dev in NetworkManager.NetworkManager.GetDevices():
        if dev.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
            continue
        for ap in dev.SpecificDevice().GetAccessPoints():
            aps.append({'ssid': ap.Ssid,
                        'connect_path': urllib.parse.quote_plus(ap.Ssid),
                        'strength': ord(ap.Strength)})
    return aps
