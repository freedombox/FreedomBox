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
from gi.repository import GLib as glib
from gi.repository import NM as nm
import logging
import socket
import struct
import uuid


logger = logging.getLogger(__name__)

CONNECTION_TYPE_NAMES = collections.OrderedDict([
    ('802-3-ethernet', 'Ethernet'),
    ('802-11-wireless', 'Wi-Fi'),
    ('pppoe', 'PPPoE')
])


class ConnectionNotFound(Exception):
    """Network connection with a given name could not be found."""
    pass


class DeviceNotFound(Exception):
    """Network device for specified operation could not be found."""
    pass


def ipv4_string_to_int(address):
    """Return an integer equivalent of a string contain IPv4 address."""
    return struct.unpack("=I", socket.inet_aton(address))[0]


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


def get_ip_from_device(devicename):
    """
    Get the first ip address from the network interface.
    will return "0.0.0.0" if no ip address is assiged.
    IP address is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    ip = "0.0.0.0"
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip4_config = device.get_ip4_config()
    if ip4_config:
        addresses = ip4_config.get_addresses()
        if addresses:
            ip = addresses.__getitem__(0).get_address()
    return ip


def get_ip6_from_device(devicename):
    """
    Get the first ip address from the network interface.
    will return "0.0.0.0" if no ip address is assiged.
    IP address is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    ip = "0.0.0.0"
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip6_config = device.get_ip6_config()
    if ip6_config:
        addresses = ip6_config.get_addresses()
        if addresses:
            ip = addresses.__getitem__(0).get_address()
    return ip


def get_all_ip_from_device(devicename):
    """
    Get all ipv4 addresses from device
    IP address is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    ip = []
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip4_config = device.get_ip4_config()
    if ip4_config:
        addresses = ip4_config.get_addresses()
        for address in addresses:
            netmask = str(address.get_prefix())
            ip.append(str(address.get_address() + "/" + netmask))
    return ip


def get_all_ip6_from_device(devicename):
    """
    Get all ipv6 addresses from device
    IP address is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    ip = []
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip6_config = device.get_ip6_config()
    if ip6_config:
        addresses = ip6_config.get_addresses()
        for address in addresses:
            netmask = str(address.get_prefix())
            ip.append(str(address.get_address() + "/" + netmask))
    return ip


def get_namesever_from_device(devicename):
    """
    Get all nameservers which are reachable via this device.
    Nameservers is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    nameservers = ""
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip4_config = device.get_ip4_config()
    if ip4_config:
        nameservers = ip4_config.get_nameservers()
    return nameservers


def get_namesever6_from_device(devicename):
    """
    Get all nameservers which are reachable via this device.
    Nameservers is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    nameservers = ""
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip6_config = device.get_ip6_config()
    if ip6_config:
        nameservers = ip6_config.get_nameservers()
    return nameservers


def get_gateway_from_device(devicename):
    """
    Get the default Gateway for this device.
    gateway is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    gateway = ""
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip4_config = device.get_ip4_config()
    if ip4_config:
        gateway = device.get_ip4_config().get_gateway()
    return gateway


def get_gateway6_from_device(devicename):
    """
    Get the default Gateway for this device.
    gateway is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    gateway = ""
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip6_config = device.get_ip6_config()
    if ip6_config:
        gateway = device.get_ip6_config().get_gateway()
    return gateway


def get_linkstate_from_device(devicename):
    """
    Get the physical link state from this device (carrier detected)
    link state is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    linkstate = False
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip4_config = device.get_ip4_config()
    if ip4_config:
        linkstate = device.get_carrier()
    return linkstate


def get_mac_from_device(devicename):
    """
    Get the MAC address of the network interface.
    MAC address is a optional information, will not raise a exception
    if no information could be returned.
    ToDo: will not work when connection is or previously was inactive
    """
    mac = "00:00:00:00:00:00"
    device = nm.Client.new(None).get_device_by_iface(devicename)
    ip4_config = device.get_ip4_config()
    if ip4_config:
        mac = device.get_hw_address()
    return mac


def connection_is_active(connection_uuid):
    """
    Return True if connection is active
    Return False if connection is inactive
    """
    client = nm.Client.new(None)
    for connection in client.get_active_connections():
        if connection.get_uuid() == connection_uuid:
            return True
    return False


def get_primary_connection():
    """return the name of the primary (aka internet) connection"""
    return nm.Client.new(None).get_primary_connection()


def get_wifi_signal(devicename, ssid):
    """Get the wifi signal strenght form a particular SSID"""
    signal = 0
    device = nm.Client.new(None).get_device_by_iface(devicename)
    for ap in device.get_access_points():
        if ap.get_ssid().get_data() == ssid:
            signal = ap.get_strength()
    return signal


def get_wifi_rate(devicename, ssid):
    """Get the wifi bitrate form a particular SSID"""
    device = nm.Client.new(None).get_device_by_iface(devicename)
    rate = device.get_bitrate() / 1000
    rate = str(str(rate) + "Mbit/s")
    return rate


def get_wifi_channel(devicename, ssid):
    """Get the wifi channeö form a particular SSID"""
    channel = 0
    device = nm.Client.new(None).get_device_by_iface(devicename)
    for ap in device.get_access_points():
        if ap.get_ssid().get_data() == ssid:
            frequency = ap.get_frequency()
    frequency = frequency / 1000

    """
    Hard coded list of wifi frequencys and their corresponding channel numbers.
    ToDo: search for a better solution! Even 5GHz is not included yet.
    Only the plain frequency will show up on 5GHz AP's.
    """
    if frequency == 2.412:
        channel = 1
    elif frequency == 2.417:
        channel = 2
    elif frequency == 2.422:
        channel = 3
    elif frequency == 2.427:
        channel = 4
    elif frequency == 2.432:
        channel = 5
    elif frequency == 2.437:
        channel = 6
    elif frequency == 2.442:
        channel = 7
    elif frequency == 2.447:
        channel = 8
    elif frequency == 2.452:
        channel = 9
    elif frequency == 2.457:
        channel = 10
    elif frequency == 2.462:
        channel = 11
    else:
        channel = str(str(frequency) + "GHz")

    return channel


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
        connection_type = CONNECTION_TYPE_NAMES.get(connection_type,
                                                    connection_type)
        connections.append({
            'name': connection.get_id(),
            'uuid': connection.get_uuid(),
            'type': connection_type,
            'is_active': connection.get_uuid() in active_uuids,
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


def _update_common_settings(connection, connection_uuid, name, type_, interface,
                            zone):
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
    settings.set_property(nm.SETTING_CONNECTION_ID, name)
    settings.set_property(nm.SETTING_CONNECTION_TYPE, type_)
    settings.set_property(nm.SETTING_CONNECTION_INTERFACE_NAME, interface)
    settings.set_property(nm.SETTING_CONNECTION_ZONE, zone)

    return connection


def _update_ipv4_settings(connection, ipv4_method, ipv4_address):
    """Edit IPv4 settings for network manager connections."""
    settings = connection.get_setting_ip4_config()
    if not settings:
        settings = nm.SettingIP4Config.new()
        connection.add_setting(settings)

    settings.set_property(nm.SETTING_IP_CONFIG_METHOD, ipv4_method)
    if ipv4_method == nm.SETTING_IP4_CONFIG_METHOD_MANUAL and ipv4_address:
        ipv4_address_int = ipv4_string_to_int(ipv4_address)
        ipv4_prefix = nm.utils_ip4_get_default_prefix(ipv4_address_int)

        address = nm.IPAddress.new(socket.AF_INET, ipv4_address, ipv4_prefix)
        settings.add_address(address)

        settings.set_property(nm.SETTING_IP_CONFIG_GATEWAY, '0.0.0.0')
    else:
        settings.clear_addresses()


def _update_ethernet_settings(connection, connection_uuid, name, interface,
                              zone, ipv4_method, ipv4_address):
    """Create/edit ethernet settings for network manager connections."""
    type_ = '802-3-ethernet'

    connection = _update_common_settings(connection, connection_uuid, name,
                                         type_, interface, zone)
    _update_ipv4_settings(connection, ipv4_method, ipv4_address)

    # Ethernet
    settings = connection.get_setting_wired()
    if not settings:
        settings = nm.SettingWired.new()
        connection.add_setting(settings)

    return connection


def _update_pppoe_settings(connection, connection_uuid, name, interface, zone,
                           username, password):
    """Create/edit PPPoE settings for network manager connections."""
    type_ = 'pppoe'

    connection = _update_common_settings(connection, connection_uuid, name,
                                         type_, interface, zone)

    # PPPoE
    settings = connection.get_setting_pppoe()
    if not settings:
        settings = nm.SettingPppoe.new()
        connection.add_setting(settings)

    settings.set_property(nm.SETTING_PPPOE_USERNAME, username)
    settings.set_property(nm.SETTING_PPPOE_PASSWORD, password)

    settings = connection.get_setting_ppp()
    if not settings:
        settings = nm.SettingPpp.new()
        connection.add_setting(settings)

    # TODO: make this configurable? Some PPP peers don't respond to
    # echo requests according to NetworkManager documentation.
    settings.set_property(nm.SETTING_PPP_LCP_ECHO_FAILURE, 5)
    settings.set_property(nm.SETTING_PPP_LCP_ECHO_INTERVAL, 30)

    return connection


def add_pppoe_connection(name, interface, zone, username, password):
    """Add an automatic PPPoE connection in network manager.

    Return the UUID for the connection.
    """
    connection_uuid = str(uuid.uuid4())
    connection = _update_pppoe_settings(
        None, connection_uuid, name, interface, zone, username, password)
    client = nm.Client.new(None)
    client.add_connection_async(connection, True, None, _callback, None)
    return connection_uuid


def edit_pppoe_connection(connection, name, interface, zone, username,
                          password):
    """Edit an existing pppoe connection in network manager."""
    _update_pppoe_settings(
        connection, connection.get_uuid(), name, interface, zone, username,
        password)
    connection.commit_changes(True)


def add_ethernet_connection(name, interface, zone, ipv4_method, ipv4_address):
    """Add an automatic ethernet connection in network manager.

    Return the UUID for the connection.
    """
    connection_uuid = str(uuid.uuid4())
    connection = _update_ethernet_settings(
        None, connection_uuid, name, interface, zone, ipv4_method,
        ipv4_address)
    client = nm.Client.new(None)
    client.add_connection_async(connection, True, None, _callback, None)
    return connection_uuid


def edit_ethernet_connection(connection, name, interface, zone, ipv4_method,
                             ipv4_address):
    """Edit an existing ethernet connection in network manager."""
    _update_ethernet_settings(
        connection, connection.get_uuid(), name, interface, zone, ipv4_method,
        ipv4_address)
    connection.commit_changes(True)


def _update_wifi_settings(connection, connection_uuid, name, interface, zone,
                          ssid, mode, auth_mode, passphrase, ipv4_method,
                          ipv4_address):
    """Create/edit wifi settings for network manager connections."""
    type_ = '802-11-wireless'
    key_mgmt = 'wpa-psk'

    connection = _update_common_settings(connection, connection_uuid, name,
                                         type_, interface, zone)
    _update_ipv4_settings(connection, ipv4_method, ipv4_address)

    # Wireless
    settings = connection.get_setting_wireless()
    if not settings:
        settings = nm.SettingWireless.new()
        connection.add_setting(settings)

    ssid_gbytes = glib.Bytes.new(ssid.encode())
    settings.set_property(nm.SETTING_WIRELESS_SSID, ssid_gbytes)
    settings.set_property(nm.SETTING_WIRELESS_MODE, mode)

    # Wireless Security
    if auth_mode == 'wpa' and passphrase:
        settings = connection.get_setting_wireless_security()
        if not settings:
            settings = nm.SettingWirelessSecurity.new()
            connection.add_setting(settings)

        settings.set_property(nm.SETTING_WIRELESS_SECURITY_KEY_MGMT, key_mgmt)
        settings.set_property(nm.SETTING_WIRELESS_SECURITY_PSK, passphrase)
    else:
        connection.remove_setting(nm.SettingWirelessSecurity)

    return connection


def add_wifi_connection(name, interface, zone, ssid, mode, auth_mode,
                        passphrase, ipv4_method, ipv4_address):
    """Add an automatic Wi-Fi connection in network manager.

    Return the UUID for the connection.
    """
    connection_uuid = str(uuid.uuid4())
    connection = _update_wifi_settings(
        None, connection_uuid, name, interface, zone, ssid, mode, auth_mode,
        passphrase, ipv4_method, ipv4_address)
    client = nm.Client.new(None)
    client.add_connection_async(connection, True, None, _callback, None)
    return connection_uuid


def edit_wifi_connection(connection, name, interface, zone, ssid, mode,
                         auth_mode, passphrase, ipv4_method, ipv4_address):
    """Edit an existing wifi connection in network manager."""
    _update_wifi_settings(
        connection, connection.get_uuid(), name, interface, zone, ssid, mode,
        auth_mode, passphrase, ipv4_method, ipv4_address)
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
                'ssid': ssid_string,
                'strength': access_point.get_strength()})

    return access_points
