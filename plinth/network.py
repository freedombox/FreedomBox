# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Helper functions for working with network manager.
"""

import collections
import logging
import socket
import struct
import time
import uuid

from django.utils.translation import gettext_lazy as _

from plinth.utils import import_from_gi

glib = import_from_gi('GLib', '2.0')
nm = import_from_gi('NM', '1.0')

logger = logging.getLogger(__name__)

_client = None

ZONES = [('external', _('External')), ('internal', _('Internal'))]

CONNECTION_TYPE_NAMES = collections.OrderedDict([
    ('802-3-ethernet', _('Ethernet')),
    ('802-11-wireless', _('Wi-Fi')),
    ('pppoe', _('PPPoE')),
    ('generic', _('Generic')),
])


class ConnectionNotFound(Exception):
    """Network connection with a given name could not be found."""


class DeviceNotFound(Exception):
    """Network device for specified operation could not be found."""


def ipv4_string_to_int(address):
    """Return an integer equivalent of a string contain IPv4 address."""
    return struct.unpack('=I', socket.inet_aton(address))[0]


def ipv4_int_to_string(address_int):
    """Return an string equivalent of a integer IPv4 address."""
    return socket.inet_ntoa(struct.pack('=I', address_int))


def init():
    """Create and keep a network manager client instance."""

    def new_callback(source_object, result, user_data):
        """Called when new() operation is complete."""
        global _client
        _client = nm.Client.new_finish(result)
        logger.info('Created Network manager client')

    logger.info('Creating network manager client')
    nm.Client.new_async(None, new_callback, None)


def get_nm_client():
    """Return a network manager client object."""
    if _client:
        return _client

    raise Exception('Client not yet ready')


def _callback(source_object, result, user_data):
    """Called when an operation is completed."""
    del source_object  # Unused
    del result  # Unused
    del user_data  # Unused


def get_interface_list(device_type):
    """Get a list of network interface available on the system."""
    interfaces = {}
    for device in get_nm_client().get_devices():
        if device.get_device_type() == device_type:
            interfaces[device.get_iface()] = device.get_hw_address()

    return interfaces


def _is_primary(connection):
    """Return whether a connection is primary connection."""
    primary = get_nm_client().get_primary_connection()
    return (primary and primary.get_uuid() == connection.get_uuid())


def get_status_from_connection(connection):
    """Return the current status of a connection."""
    status = collections.defaultdict(dict)

    status['id'] = connection.get_id()
    status['uuid'] = connection.get_uuid()
    status['type'] = connection.get_connection_type()
    status['zone'] = connection.get_setting_connection().get_zone()
    status['dns_over_tls'] = \
        connection.get_setting_connection().get_dns_over_tls().value_nick
    status['interface_name'] = connection.get_interface_name()
    status['primary'] = _is_primary(connection)

    status['ipv4']['method'] = connection.get_setting_ip4_config().get_method()
    status['ipv6']['method'] = connection.get_setting_ip6_config().get_method()

    if status['type'] == '802-11-wireless':
        setting_wireless = connection.get_setting_wireless()
        status['wireless']['ssid'] = setting_wireless.get_ssid().get_data(
        ).decode()
        status['wireless']['mode'] = setting_wireless.get_mode()

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
        status['ip4']['addresses'] = [{
            'address': address.get_address(),
            'prefix': address.get_prefix()
        } for address in addresses]
        status['ip4']['gateway'] = ip4_config.get_gateway()
        status['ip4']['nameservers'] = ip4_config.get_nameservers()

    ip6_config = device.get_ip6_config()
    if ip6_config:
        addresses = ip6_config.get_addresses()
        status['ip6']['addresses'] = [{
            'address': address.get_address(),
            'prefix': address.get_prefix()
        } for address in addresses]
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
           access_point.get_ssid().get_data().decode() == ssid:
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
    channel_map = {
        2412: 1,
        2417: 2,
        2422: 3,
        2427: 4,
        2432: 5,
        2437: 6,
        2442: 7,
        2447: 8,
        2452: 9,
        2457: 10,
        2462: 11
    }
    try:
        return channel_map[frequency]
    except KeyError:
        return str(frequency / 1000) + 'GHz'


def get_connection_list():
    """Get a list of active and available connections."""
    client = get_nm_client()
    primary_connection = client.get_primary_connection()

    active_uuids = []
    for connection in client.get_active_connections():
        active_uuids.append(connection.get_uuid())

    connections = []
    for connection in client.get_connections():
        # Display a friendly type name if known.
        connection_type = connection.get_connection_type()
        # Do not show bridge adapter as it is not meant to
        # be modified by the user.
        if connection_type == 'bridge':
            continue

        connection_type_name = CONNECTION_TYPE_NAMES.get(
            connection_type, connection_type)

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
            'primary':
                (primary_connection
                 and primary_connection.get_uuid() == connection.get_uuid()),
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
    client = get_nm_client()
    connection = client.get_connection_by_uuid(connection_uuid)
    if not connection:
        raise ConnectionNotFound(connection_uuid)

    return connection


def get_active_connection(connection_uuid):
    """Return active connection with matching UUID.

    Raise ConnectionNotFound if a connection with that uuid is not
    found.
    """
    connections = get_nm_client().get_active_connections()
    connections = {
        connection.get_uuid(): connection
        for connection in connections
    }
    try:
        return connections[connection_uuid]
    except KeyError:
        raise ConnectionNotFound(connection_uuid)


def get_connection_by_interface_name(interface_name):
    """Return connection with matching interface.

    Return None if a connection with the interface is not found."""
    client = get_nm_client()
    for connection in client.get_connections():
        if connection.get_interface_name() == interface_name:
            return connection

    return None


def get_device_by_interface_name(interface_name):
    """Return a device by interface name."""
    return get_nm_client().get_device_by_iface(interface_name)


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
    if 'name' in common:
        settings.set_property(nm.SETTING_CONNECTION_ID, common['name'])

    if 'type' in common:
        settings.set_property(nm.SETTING_CONNECTION_TYPE, common['type'])

    if 'interface' in common:
        settings.set_property(nm.SETTING_CONNECTION_INTERFACE_NAME,
                              common['interface'])

    if 'zone' in common:
        settings.set_property(nm.SETTING_CONNECTION_ZONE, common['zone'])

    if 'dns_over_tls' in common:
        values = {
            'default': nm.SettingConnectionDnsOverTls.DEFAULT,
            'no': nm.SettingConnectionDnsOverTls.NO,
            'opportunistic': nm.SettingConnectionDnsOverTls.OPPORTUNISTIC,
            'yes': nm.SettingConnectionDnsOverTls.YES
        }
        settings.set_property(nm.SETTING_CONNECTION_DNS_OVER_TLS,
                              values[common['dns_over_tls']])

    if 'autoconnect' in common:
        settings.set_property(nm.SETTING_CONNECTION_AUTOCONNECT,
                              common['autoconnect'])

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


def _update_wireguard_settings(connection, wireguard):
    """Create/edit WireGuard settings for network manager connections."""
    settings = connection.get_setting_by_name('wireguard')
    if not settings:
        settings = nm.SettingWireGuard.new()
        connection.add_setting(settings)

    settings.set_property(nm.SETTING_WIREGUARD_PRIVATE_KEY,
                          wireguard['private_key'])
    if 'listen_port' in wireguard:
        settings.set_property(nm.SETTING_WIREGUARD_LISTEN_PORT,
                              wireguard['listen_port'])

    if 'peer_public_key' in wireguard:
        peer = nm.WireGuardPeer.new()
        peer.set_public_key(wireguard['peer_public_key'], False)

        if 'peer_endpoint' in wireguard:
            peer.set_endpoint(wireguard['peer_endpoint'], False)

        if wireguard['preshared_key']:
            # Flag NONE means that NM should store and retain the secret.
            # Default seems to be NOT_REQUIRED in this case.
            peer.set_preshared_key_flags(nm.SettingSecretFlags.NONE)
            peer.set_preshared_key(wireguard['preshared_key'], False)

        peer.append_allowed_ip('0.0.0.0/0', False)
        peer.append_allowed_ip('::/0', False)
        settings.clear_peers()
        settings.append_peer(peer)


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

    if 'wireguard' in settings and settings['wireguard']:
        _update_wireguard_settings(connection, settings['wireguard'])

    return connection


def add_connection(settings):
    """Add an connection in network manager.

    Return the UUID for the connection.
    """
    connection_uuid = str(uuid.uuid4())
    connection = _update_settings(None, connection_uuid, settings)
    client = get_nm_client()
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
    client = get_nm_client()
    for device in client.get_all_devices():
        if device.get_iface() == interface:
            client.activate_connection_async(connection, device, '/', None,
                                             _callback, None)
            break
    else:
        raise DeviceNotFound(connection)

    return connection


def deactivate_connection(connection_uuid):
    """Find and de-activate a network connection."""
    active_connection = get_active_connection(connection_uuid)
    get_nm_client().deactivate_connection(active_connection)
    return active_connection


def reactivate_connection(connection_uuid):
    """Find and re-activate a network connection to reflect new changes.

    If connection was not active to begin with, do nothing.

    """
    try:
        deactivate_connection(connection_uuid)
    except ConnectionNotFound:
        return  # Connection was not active to start with

    # deactivate_connection() is a synchronous call. However, it returns before
    # the connection is fully deactivated. When re-activating such connections,
    # sometimes, we get a "Authorization request cancelled" error. So, wait
    # until the connection is fully deactivated. XXX: Perform proper
    # asynchronous waiting instead of polling. Also find a way to avoid the
    # problem altogether.
    for index in range(10):  # pylint: disable=unused-variable
        try:
            get_active_connection(connection_uuid)
            time.sleep(0.1)
        except ConnectionNotFound:
            break

    activate_connection(connection_uuid)


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
    for device in get_nm_client().get_devices():
        if device.get_device_type() != nm.DeviceType.WIFI:
            continue

        for access_point in device.get_access_points():
            # Retrieve the bytes in SSID.  Don't convert to utf-8 or
            # escape it in any way as it may contain null bytes.  When
            # this is used in the URL it will be escaped properly and
            # unescaped when taken as view function's argument.
            ssid = access_point.get_ssid()
            ssid_string = ssid.get_data().decode() if ssid else ''
            access_points.append({
                'interface_name': device.get_iface(),
                'ssid': ssid_string,
                'strength': access_point.get_strength()
            })

    return access_points


def refeed_dns():
    """Re-feed DNS servers to systemd-resolved."""
    get_nm_client().reload(nm.ManagerReloadFlags.DNS_RC)
