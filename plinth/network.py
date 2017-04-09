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

import collections
from django.utils.translation import ugettext_lazy as _
import logging
import socket
import struct
import subprocess
import uuid

from plinth.utils import import_from_gi
glib = import_from_gi('GLib', '2.0')
nm = import_from_gi('NM', '1.0')

logger = logging.getLogger(__name__)

CONNECTION_TYPE_NAMES = collections.OrderedDict([
    ('802-3-ethernet', _('Ethernet')),
    ('802-11-wireless', _('Wi-Fi')),
    ('pppoe', _('PPPoE')),
    ('generic', _('Generic')),
])


class ConnectionNotFound(Exception):
    """Network connection with a given name could not be found."""
    pass


class DeviceNotFound(Exception):
    """Network device for specified operation could not be found."""
    pass


def ipv4_string_to_int(address):
    """Return an integer equivalent of a string contain IPv4 address."""
    return struct.unpack('=I', socket.inet_aton(address))[0]


def ipv4_int_to_string(address_int):
    """Return an string equivalent of a integer IPv4 address."""
    return socket.inet_ntoa(struct.pack('=I', address_int))


def _callback(source_object, result, user_data):
    """Called when an operation is completed."""
    del source_object  # Unused
    del result  # Unused
    del user_data  # Unused


def _commit_callback(connection, error, data=None):
    """Called when the connection changes are committed."""
    del connection
    del error
    del data


def get_interface_list(device_type):
    """Get a list of network interface available on the system."""
    interfaces = {}
    for device in nm.Client.new(None).get_devices():
        if device.get_device_type() == device_type:
            interfaces[device.get_iface()] = device.get_hw_address()

    return interfaces


def get_status_from_connection(connection):
    """Return the current status of a connection."""
    status = collections.defaultdict(dict)

    status['id'] = connection.get_id()
    status['uuid'] = connection.get_uuid()
    status['type'] = connection.get_connection_type()
    status['zone'] = connection.get_setting_connection().get_zone()
    status['interface_name'] = connection.get_interface_name()

    status['ipv4']['method'] = connection.get_setting_ip4_config().get_method()
    status['ipv6']['method'] = connection.get_setting_ip6_config().get_method()

    if status['type'] == '802-11-wireless':
        setting_wireless = connection.get_setting_wireless()
        status['wireless']['ssid'] = setting_wireless.get_ssid().get_data()

    primary_connection = nm.Client.new(None).get_primary_connection()
    status['primary'] = (
        primary_connection and
        primary_connection.get_uuid() == connection.get_uuid()
    )

    return status


def get_status_from_active_connection(connection):
    """Return the current status of an active connection."""
    status = collections.defaultdict(dict)

    status['state'] = connection.get_state().value_name
    status['ip4']['default'] = connection.get_default()
    status['ip6']['default'] = connection.get_default6()

    return status


def get_status_from_device(device):
    """Return a dictionary with current status of a network device."""
    if not device:
        return None

    status = collections.defaultdict(dict)

    ip4_config = device.get_ip4_config()
    if ip4_config:
        addresses = ip4_config.get_addresses()
        status['ip4']['addresses'] = [{'address': address.get_address(),
                                       'prefix': address.get_prefix()}
                                      for address in addresses]
        status['ip4']['gateway'] = ip4_config.get_gateway()
        status['ip4']['nameservers'] = ip4_config.get_nameservers()

    ip6_config = device.get_ip6_config()
    if ip6_config:
        addresses = ip6_config.get_addresses()
        status['ip6']['addresses'] = [{'address': address.get_address(),
                                       'prefix': address.get_prefix()}
                                      for address in addresses]
        status['ip6']['gateway'] = ip6_config.get_gateway()
        status['ip6']['nameservers'] = ip6_config.get_nameservers()

    status['type'] = device.get_type_description()
    status['description'] = device.get_description()
    status['hw_address'] = device.get_hw_address()
    status['interface_name'] = device.get_iface()
    status['state'] = device.get_state().value_nick
    status['state_reason'] = device.get_state_reason().value_nick

    if device.get_device_type() == nm.DeviceType.WIFI:
        status['wireless']['bitrate'] = device.get_bitrate() / 1000
        status['wireless']['mode'] = device.get_mode().value_nick

    if device.get_device_type() == nm.DeviceType.ETHERNET:
        status['ethernet']['speed'] = device.get_speed()
        status['ethernet']['carrier'] = device.get_carrier()

    return status


def get_status_from_wifi_access_point(device, ssid):
    """Return the current status of an access point."""
    status = {}

    if not ssid or not device:
        return status

    for access_point in device.get_access_points():
        if access_point and access_point.get_ssid() and \
           access_point.get_ssid().get_data() == ssid:
            status['strength'] = access_point.get_strength()
            frequency = access_point.get_frequency()
            status['channel'] = _get_wifi_channel_from_frequency(frequency)
            break

    return status


def _get_wifi_channel_from_frequency(frequency):
    """Get the wifi channel form a particular SSID"""
    # TODO: Hard coded list of wifi frequencys and their corresponding
    # channel numbers.  Search for a better solution!  Even 5GHz is
    # not included yet.  Only the plain frequency will show up on 5GHz
    # AP's.
    channel_map = {2412: 1, 2417: 2, 2422: 3, 2427: 4, 2432: 5, 2437: 6,
                   2442: 7, 2447: 8, 2452: 9, 2457: 10, 2462: 11}
    try:
        return channel_map[frequency]
    except KeyError:
        return str(frequency / 1000) + 'GHz'


def get_connection_list():
    """Get a list of active and available connections."""
    active_uuids = []
    client = nm.Client.new(None)
    for connection in client.get_active_connections():
        active_uuids.append(connection.get_uuid())

    connections = []
    for connection in client.get_connections():
        # Display a friendly type name if known.
        connection_type = connection.get_connection_type()
        connection_type_name = CONNECTION_TYPE_NAMES.get(connection_type,
                                                         connection_type)

        settings_connection = connection.get_setting_connection()
        zone = settings_connection.get_zone()

        connection.get_interface_name()

        connections.append({
            'name': connection.get_id(),
            'uuid': connection.get_uuid(),
            'interface_name': connection.get_interface_name(),
            'type': connection_type,
            'type_name': connection_type_name,
            'is_active': connection.get_uuid() in active_uuids,
            'zone': zone,
        })
    connections.sort(key=lambda connection: connection['is_active'],
                     reverse=True)
    return connections


def get_connection(connection_uuid):
    """Return connection with matching uuid.

    Raise ConnectionNotFound if a connection with that uuid is not
    found.
    """
    client = nm.Client.new(None)
    connection = client.get_connection_by_uuid(connection_uuid)
    if not connection:
        raise ConnectionNotFound(connection_uuid)

    return connection


def get_active_connection(connection_uuid):
    """Return active connection with matching UUID.

    Raise ConnectionNotFound if a connection with that uuid is not
    found.
    """
    connections = nm.Client.new(None).get_active_connections()
    connections = {connection.get_uuid(): connection
                   for connection in connections}
    try:
        return connections[connection_uuid]
    except KeyError:
        raise ConnectionNotFound(connection_uuid)


def get_device_by_interface_name(interface_name):
    """Return a device by interface name."""
    return nm.Client.new(None).get_device_by_iface(interface_name)


def _update_common_settings(connection, connection_uuid, common):
    """Create/edit basic settings for network manager connections.

    Return newly created connection object if connection is None.
    """
    if not connection:
        connection = nm.SimpleConnection.new()

    settings = connection.get_setting_connection()
    if not settings:
        settings = nm.SettingConnection.new()
        connection.add_setting(settings)

    settings.set_property(nm.SETTING_CONNECTION_UUID, connection_uuid)
    settings.set_property(nm.SETTING_CONNECTION_ID, common['name'])
    settings.set_property(nm.SETTING_CONNECTION_TYPE, common['type'])
    settings.set_property(nm.SETTING_CONNECTION_INTERFACE_NAME,
                          common['interface'])
    settings.set_property(nm.SETTING_CONNECTION_ZONE, common['zone'])

    return connection


def _update_ipv4_settings(connection, ipv4):
    """Edit IPv4 settings for network manager connections."""
    settings = nm.SettingIP4Config.new()
    connection.add_setting(settings)

    settings.set_property(nm.SETTING_IP_CONFIG_METHOD, ipv4['method'])
    if (ipv4['method'] == nm.SETTING_IP4_CONFIG_METHOD_MANUAL or
        ipv4['method'] == nm.SETTING_IP4_CONFIG_METHOD_SHARED) and \
       ipv4['address']:
        ipv4_address_int = ipv4_string_to_int(ipv4['address'])

        if not ipv4['netmask']:
            ipv4_netmask_int = nm.utils_ip4_get_default_prefix(
                ipv4_address_int)
        else:
            ipv4_netmask_int = nm.utils_ip4_netmask_to_prefix(
                ipv4_string_to_int(ipv4['netmask']))

        address = nm.IPAddress.new(socket.AF_INET, ipv4['address'],
                                   ipv4_netmask_int)
        settings.add_address(address)

        if not ipv4['gateway']:
            settings.set_property(nm.SETTING_IP_CONFIG_GATEWAY, '0.0.0.0')
        else:
            settings.set_property(nm.SETTING_IP_CONFIG_GATEWAY,
                                  ipv4['gateway'])
    else:
        if ipv4['dns'] or ipv4['second_dns']:
            settings.set_property(nm.SETTING_IP_CONFIG_IGNORE_AUTO_DNS, True)

    if ipv4['dns']:
        settings.add_dns(ipv4['dns'])

    if ipv4['second_dns']:
        settings.add_dns(ipv4['second_dns'])


def _update_ipv6_settings(connection, ipv6):
    """Edit IPv6 settings for network manager connections."""
    settings = nm.SettingIP6Config.new()
    connection.add_setting(settings)

    settings.set_property(nm.SETTING_IP_CONFIG_METHOD, ipv6['method'])
    if ipv6['method'] == nm.SETTING_IP6_CONFIG_METHOD_MANUAL and \
       ipv6['address'] and ipv6['prefix']:
        address = nm.IPAddress.new(socket.AF_INET6, ipv6['address'],
                                   int(ipv6['prefix']))
        settings.add_address(address)

        if not ipv6['gateway']:
            settings.set_property(nm.SETTING_IP_CONFIG_GATEWAY, '::')
        else:
            settings.set_property(nm.SETTING_IP_CONFIG_GATEWAY,
                                  ipv6['gateway'])
    else:
        if ipv6['dns'] or ipv6['second_dns']:
            settings.set_property(nm.SETTING_IP_CONFIG_IGNORE_AUTO_DNS, True)

    if ipv6['dns']:
        settings.add_dns(ipv6['dns'])

    if ipv6['second_dns']:
        settings.add_dns(ipv6['second_dns'])


def _update_pppoe_settings(connection, pppoe):
    """Create/edit PPPoE settings for network manager connections."""
    # PPPoE
    settings = connection.get_setting_pppoe()
    if not settings:
        settings = nm.SettingPppoe.new()
        connection.add_setting(settings)

    settings.set_property(nm.SETTING_PPPOE_USERNAME, pppoe['username'])
    settings.set_property(nm.SETTING_PPPOE_PASSWORD, pppoe['password'])

    settings = connection.get_setting_ppp()
    if not settings:
        settings = nm.SettingPpp.new()
        connection.add_setting(settings)

    # TODO: make this configurable? Some PPP peers don't respond to
    # echo requests according to NetworkManager documentation.
    settings.set_property(nm.SETTING_PPP_LCP_ECHO_FAILURE, 5)
    settings.set_property(nm.SETTING_PPP_LCP_ECHO_INTERVAL, 30)

    return connection


def _update_wireless_settings(connection, wireless):
    """Create/edit wifi settings for network manager connections."""
    key_mgmt = 'wpa-psk'

    # Wireless
    settings = connection.get_setting_wireless()
    if not settings:
        settings = nm.SettingWireless.new()
        connection.add_setting(settings)

    ssid_gbytes = glib.Bytes.new(wireless['ssid'].encode())
    settings.set_property(nm.SETTING_WIRELESS_SSID, ssid_gbytes)
    settings.set_property(nm.SETTING_WIRELESS_MODE, wireless['mode'])
    band = wireless['band'] if wireless['band'] != 'auto' else None
    settings.set_property(nm.SETTING_WIRELESS_BAND, band)
    channel = wireless['channel']
    if wireless['band'] == 'auto' or not wireless['channel']:
        channel = 0

    settings.set_property(nm.SETTING_WIRELESS_CHANNEL, channel)
    settings.set_property(nm.SETTING_WIRELESS_BSSID, wireless['bssid'] or None)

    # Wireless Security
    if wireless['auth_mode'] == 'wpa' and wireless['passphrase']:
        settings = connection.get_setting_wireless_security()
        if not settings:
            settings = nm.SettingWirelessSecurity.new()
            connection.add_setting(settings)

        settings.set_property(nm.SETTING_WIRELESS_SECURITY_KEY_MGMT, key_mgmt)
        settings.set_property(nm.SETTING_WIRELESS_SECURITY_PSK,
                              wireless['passphrase'])
    else:
        connection.remove_setting(nm.SettingWirelessSecurity)

    return connection


def _update_settings(connection, connection_uuid, settings):
    """Create/edit wifi settings for network manager connections."""
    connection = _update_common_settings(connection, connection_uuid,
                                         settings['common'])
    if 'ipv4' in settings and settings['ipv4']:
        _update_ipv4_settings(connection, settings['ipv4'])

    if 'ipv6' in settings and settings['ipv6']:
        _update_ipv6_settings(connection, settings['ipv6'])

    if 'pppoe' in settings and settings['pppoe']:
        _update_pppoe_settings(connection, settings['pppoe'])

    if 'wireless' in settings and settings['wireless']:
        _update_wireless_settings(connection, settings['wireless'])

    return connection


def add_connection(settings):
    """Add an connection in network manager.

    Return the UUID for the connection.
    """
    connection_uuid = str(uuid.uuid4())
    connection = _update_settings(None, connection_uuid, settings)
    client = nm.Client.new(None)
    client.add_connection_async(connection, True, None, _callback, None)
    return connection_uuid


def edit_connection(connection, settings):
    """Edit an existing connection in network manager."""
    _update_settings(connection, connection.get_uuid(), settings)
    connection.commit_changes(True)


def activate_connection(connection_uuid):
    """Find and activate a network connection."""
    connection = get_connection(connection_uuid)
    interface = connection.get_interface_name()
    client = nm.Client.new(None)
    for device in client.get_devices():
        if device.get_iface() == interface:
            client.activate_connection_async(
                connection, device, '/', None, _callback, None)
            break
    else:
        raise DeviceNotFound(connection)

    return connection


def deactivate_connection(connection_uuid):
    """Find and de-activate a network connection."""
    active_connection = get_active_connection(connection_uuid)
    nm.Client.new(None).deactivate_connection(active_connection)
    return active_connection


def delete_connection(connection_uuid):
    """Delete an exiting connection from network manager.

    Raise ConnectionNotFound if connection does not exist.
    """
    connection = get_connection(connection_uuid)
    name = connection.get_id()
    connection.delete()
    return name


def wifi_scan():
    """Scan for available access points across all Wi-Fi devices."""
    access_points = []
    for device in nm.Client.new(None).get_devices():
        if device.get_device_type() != nm.DeviceType.WIFI:
            continue

        for access_point in device.get_access_points():
            # Retrieve the bytes in SSID.  Don't convert to utf-8 or
            # escape it in any way as it may contain null bytes.  When
            # this is used in the URL it will be escaped properly and
            # unescaped when taken as view function's argument.
            ssid = access_point.get_ssid()
            ssid_string = ssid.get_data() if ssid else ''
            access_points.append({
                'interface_name': device.get_iface(),
                'ssid': ssid_string,
                'strength': access_point.get_strength()})

    return access_points
