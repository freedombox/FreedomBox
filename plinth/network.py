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
import logging
import NetworkManager
import uuid


logger = logging.getLogger(__name__)

CONNECTION_TYPE_NAMES = {
    '802-3-ethernet': 'Ethernet',
    '802-11-wireless': 'Wi-Fi',
}


class ConnectionNotFound(Exception):
    """Network connection with a given name could not be found."""
    pass


class DeviceNotFound(Exception):
    """Network device for specified operation could not be found."""
    pass


def get_connection_list():
    """Get a list of active and available connections."""
    active_uuids = []
    for connection in NetworkManager.NetworkManager.ActiveConnections:
        try:
            settings = connection.Connection.GetSettings()['connection']
        except DBusException:
            # DBusException can be thrown here if the connection list is loaded
            # quickly after a connection is deactivated.
            continue

        active_uuids.append(settings['uuid'])

    connections = []
    for connection in NetworkManager.Settings.ListConnections():
        settings = connection.GetSettings()['connection']
        # Display a friendly type name if known.
        connection_type = CONNECTION_TYPE_NAMES.get(settings['type'],
                                                    settings['type'])
        connections.append({
            'name': settings['id'],
            'uuid': settings['uuid'],
            'type': connection_type,
            'is_active': settings['uuid'] in active_uuids,
        })
    connections.sort(key=lambda connection: connection['is_active'],
                     reverse=True)
    return connections


def get_connection(uuid):
    """Return connection with matching uuid.

    Raise ConnectionNotFound if a connection with that uuid is not found.
    """
    connections = NetworkManager.Settings.ListConnections()
    connections = {connection.GetSettings()['connection']['uuid']: connection
                   for connection in connections}
    try:
        return connections[uuid]
    except KeyError:
        raise ConnectionNotFound(uuid)


def get_active_connection(uuid):
    """Returns active connection with matching uuid.

    Raise ConnectionNotFound if a connection with that uuid is not found.
    """
    connections = NetworkManager.NetworkManager.ActiveConnections
    connections = {connection.Connection.GetSettings()['connection']['uuid']:
                   connection for connection in connections}
    try:
        return connections[uuid]
    except KeyError:
        raise ConnectionNotFound(uuid)


def _create_ethernet_settings(uuid, name, zone, ipv4_method, ipv4_address):
    """Create an Ethernet setting structure in network manager format."""
    settings = {
        'connection': {
            'id': name,
            'type': '802-3-ethernet',
            'zone': zone,
            'uuid': uuid,
        },
        '802-3-ethernet': {},
        'ipv4': {'method': ipv4_method},
    }

    if ipv4_method == 'manual' and ipv4_address:
        settings['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    return settings


def add_ethernet_connection(name, zone, ipv4_method, ipv4_address):
    """Add an automatic ethernet connection in network manager."""
    settings = _create_ethernet_settings(
        str(uuid.uuid4()), name, zone, ipv4_method, ipv4_address)
    NetworkManager.Settings.AddConnection(settings)
    return settings


def edit_ethernet_connection(connection, name, zone, ipv4_method,
                             ipv4_address):
    """Edit an existing ethernet connection in network manager."""
    settings = connection.GetSettings()
    new_settings = _create_ethernet_settings(
        settings['connection']['uuid'], name, zone, ipv4_method, ipv4_address)
    connection.Update(new_settings)


def _create_wifi_settings(uuid, name, zone, ssid, mode, auth_mode, passphrase,
                          ipv4_method, ipv4_address):
    """Create a Wi-Fi settings structure in network manager format."""
    settings = {
        'connection': {
            'id': name,
            'type': '802-11-wireless',
            'zone': zone,
            'uuid': uuid,
        },
        '802-11-wireless': {
            'ssid': ssid,
            'mode': mode,
        },
        'ipv4': {'method': ipv4_method},
    }

    if auth_mode == 'wpa' and passphrase:
        settings['connection']['security'] = '802-11-wireless-security'
        settings['802-11-wireless-security'] = {
            'key-mgmt': 'wpa-psk',
            'psk': passphrase,
        }

    if ipv4_method == 'manual' and ipv4_address:
        settings['ipv4']['addresses'] = [
            (ipv4_address,
             24,  # CIDR prefix length
             '0.0.0.0')]  # gateway

    return settings


def add_wifi_connection(name, zone,
                        ssid, mode, auth_mode, passphrase,
                        ipv4_method, ipv4_address):
    """Add an automatic Wi-Fi connection in network manager."""
    settings = _create_wifi_settings(
        str(uuid.uuid4()), name, zone, ssid, mode, auth_mode, passphrase,
        ipv4_method, ipv4_address)
    NetworkManager.Settings.AddConnection(settings)
    return settings


def edit_wifi_connection(connection, name, zone,
                         ssid, mode, auth_mode, passphrase,
                         ipv4_method, ipv4_address):
    """Edit an existing wifi connection in network manager."""
    settings = connection.GetSettings()
    new_settings = _create_wifi_settings(
        settings['connection']['uuid'], name, zone, ssid, mode, auth_mode,
        passphrase, ipv4_method, ipv4_address)
    connection.Update(new_settings)


def activate_connection(uuid):
    """Find and activate a network connection."""
    # Find the connection
    connection = get_connection(uuid)

    # Find a suitable device
    ctype = connection.GetSettings()['connection']['type']
    if ctype == 'vpn':
        for device in NetworkManager.NetworkManager.GetDevices():
            if device.State == NetworkManager.NM_DEVICE_STATE_ACTIVATED and \
               device.Managed:
                break
        else:
            raise DeviceNotFound(connection)
    else:
        dtype = {
            '802-11-wireless': NetworkManager.NM_DEVICE_TYPE_WIFI,
            '802-3-ethernet': NetworkManager.NM_DEVICE_TYPE_ETHERNET,
            'gsm': NetworkManager.NM_DEVICE_TYPE_MODEM,
        }.get(ctype, ctype)

        for device in NetworkManager.NetworkManager.GetDevices():
            if device.DeviceType == dtype and \
               device.State == NetworkManager.NM_DEVICE_STATE_DISCONNECTED:
                break
        else:
            raise DeviceNotFound(connection)

    NetworkManager.NetworkManager.ActivateConnection(connection, device, "/")
    return connection


def deactivate_connection(name):
    """Find and de-activate a network connection."""
    active_connection = get_active_connection(name)
    NetworkManager.NetworkManager.DeactivateConnection(active_connection)
    return active_connection


def delete_connection(uuid):
    """Delete an exiting connection from network manager.

    Raise ConnectionNotFound if connection does not exist.
    """
    connection = get_connection(uuid)
    name = connection.GetSettings()['connection']['id']
    connection.Delete()
    return name


def wifi_scan():
    """Scan for available access points across all Wi-Fi devices."""
    access_points = []
    for device in NetworkManager.NetworkManager.GetDevices():
        if device.DeviceType != NetworkManager.NM_DEVICE_TYPE_WIFI:
            continue

        for access_point in device.SpecificDevice().GetAllAccessPoints():
            access_points.append({
                'ssid': access_point.Ssid,
                'strength': access_point.Strength})

    return access_points
