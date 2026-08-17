# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for network configuration utilities.
"""

import copy
import threading
import time

import pytest

from plinth.utils import import_from_gi

ethernet_settings = {
    'common': {
        'type': '802-3-ethernet',
        'name': 'plinth_test_eth',
        'interface': 'eth0',
        'zone': 'internal',
        'dns_over_tls': 'opportunistic',
    },
    'ipv4': {
        'method': 'auto',
        'dns': '',
        'second_dns': '',
    },
    'ipv6': {
        'method': 'auto',
        'dns': '',
        'second_dns': '',
    },
}

wifi_settings = {
    'common': {
        'type': '802-11-wireless',
        'name': 'plinth_test_wifi',
        'interface': 'wlan0',
        'zone': 'external',
        'dns_over_tls': 'yes',
    },
    'ipv4': {
        'method': 'auto',
        'dns': '',
        'second_dns': '',
    },
    'ipv6': {
        'method': 'auto',
        'dns': '',
        'second_dns': '',
    },
    'wireless': {
        'ssid': 'plinthtestwifi',
        'mode': 'adhoc',
        'auth_mode': 'open',
        'band': 'a',
        'channel': 0,
        'bssid': 'a0:86:c6:08:11:02',
    },
}

pppoe_settings = {
    'common': {
        'type': 'pppoe',
        'name': 'plinth_test_pppoe',
        'interface': 'eth1',
        'zone': 'internal',
    },
    'pppoe': {
        'username': 'x-user',
        'password': 'x-password',
    },
}


@pytest.fixture(autouse=True, scope='module')
def fixture_network_module_init():
    """Initialize network module in a separate thread."""
    from plinth import network as network_module
    glib = import_from_gi('GLib', '2.0')
    main_loop = glib.MainLoop()

    def main_loop_runner():
        """Initialize the network module and run glib main loop until quit."""
        network_module.init()
        main_loop.run()

    thread = threading.Thread(target=main_loop_runner)
    thread.start()

    while not network_module._client:
        time.sleep(0.1)

    yield

    if main_loop:
        main_loop.quit()

    thread.join()


@pytest.fixture(name='network')
def fixture_network(needs_root):
    """Return the network module. Load it conservatively."""
    from plinth import network as network_module
    return network_module


def _connection(network, settings):
    """Create, yield and delete a connection."""
    uuid = network.add_connection(settings)
    time.sleep(0.1)
    yield uuid
    time.sleep(0.1)
    network.delete_connection(uuid)


@pytest.fixture(name='ethernet_uuid')
def fixture_ethernet_uuid(network):
    """Test fixture to setup and teardown an Ethernet connection."""
    yield from _connection(network, ethernet_settings)


@pytest.fixture(name='wifi_uuid')
def fixture_wifi_uuid(network):
    """Test fixture to setup and teardown an Wi-Fi connection."""
    yield from _connection(network, wifi_settings)


@pytest.fixture(name='pppoe_uuid')
def fixture_pppoe_uuid(network):
    """Test fixture to setup and teardown an PPPoE connection."""
    yield from _connection(network, pppoe_settings)


@pytest.mark.usefixtures('ethernet_uuid', 'wifi_uuid', 'pppoe_uuid')
def test_get_connection_list(network):
    """Check that we can get a list of available connections."""
    connections = network.get_connection_list()
    connection_names = [conn['name'] for conn in connections]

    assert 'plinth_test_eth' in connection_names
    assert 'plinth_test_wifi' in connection_names
    assert 'plinth_test_pppoe' in connection_names


def test_get_connection(network, ethernet_uuid, wifi_uuid):
    """Check that we can get a connection by name."""
    connection = network.get_connection(ethernet_uuid)
    assert connection.get_id() == 'plinth_test_eth'

    connection = network.get_connection(wifi_uuid)
    assert connection.get_id() == 'plinth_test_wifi'

    with pytest.raises(network.ConnectionNotFound):
        network.get_connection('x-invalid-network-id')


def test_edit_ethernet_connection(network, ethernet_uuid):
    """Check that we can update an ethernet connection."""
    connection = network.get_connection(ethernet_uuid)
    ethernet_settings2 = copy.deepcopy(ethernet_settings)
    ethernet_settings2['common']['name'] = 'plinth_test_eth_new'
    ethernet_settings2['common']['interface'] = 'eth1'
    ethernet_settings2['common']['zone'] = 'external'
    ethernet_settings2['common']['dns_over_tls'] = 'no'
    ethernet_settings2['common']['autoconnect'] = False
    ethernet_settings2['ipv4']['method'] = 'auto'
    network.edit_connection(connection, ethernet_settings2)

    connection = network.get_connection(ethernet_uuid)
    assert connection.get_id() == 'plinth_test_eth_new'

    settings_connection = connection.get_setting_connection()
    assert settings_connection.get_interface_name() == 'eth1'
    assert settings_connection.get_zone() == 'external'
    assert settings_connection.get_dns_over_tls().value_nick == 'no'
    assert not settings_connection.get_autoconnect()

    settings_ipv4 = connection.get_setting_ip4_config()
    assert settings_ipv4.get_method() == 'auto'


def test_edit_pppoe_connection(network, pppoe_uuid):
    """Check that we can update a PPPoE connection."""
    connection = network.get_connection(pppoe_uuid)
    pppoe_settings2 = copy.deepcopy(pppoe_settings)
    pppoe_settings2['common']['name'] = 'plinth_test_pppoe_new'
    pppoe_settings2['common']['interface'] = 'eth2'
    pppoe_settings2['common']['zone'] = 'external'
    pppoe_settings2['common']['autoconnect'] = False
    pppoe_settings2['pppoe']['username'] = 'x-user-new'
    pppoe_settings2['pppoe']['password'] = 'x-password-new'
    network.edit_connection(connection, pppoe_settings2)

    connection = network.get_connection(pppoe_uuid)
    assert connection.get_id() == 'plinth_test_pppoe_new'

    settings_connection = connection.get_setting_connection()
    assert settings_connection.get_interface_name() == 'eth2'
    assert settings_connection.get_zone() == 'external'
    assert not settings_connection.get_autoconnect()

    settings_pppoe = connection.get_setting_pppoe()
    assert settings_pppoe.get_username() == 'x-user-new'
    secrets = connection.get_secrets('pppoe')
    assert secrets['pppoe']['password'] == 'x-password-new'

    settings_ppp = connection.get_setting_ppp()
    assert settings_ppp.get_lcp_echo_failure() == 5
    assert settings_ppp.get_lcp_echo_interval() == 30


def test_edit_wifi_connection(network, wifi_uuid):
    """Check that we can update a wifi connection."""
    connection = network.get_connection(wifi_uuid)
    wifi_settings2 = copy.deepcopy(wifi_settings)
    wifi_settings2['common']['name'] = 'plinth_test_wifi_new'
    wifi_settings2['common']['interface'] = 'wlan1'
    wifi_settings2['common']['zone'] = 'external'
    wifi_settings2['common']['dns_over_tls'] = 'opportunistic'
    wifi_settings2['common']['autoconnect'] = False
    wifi_settings2['ipv4']['method'] = 'auto'
    wifi_settings2['wireless']['ssid'] = 'plinthtestwifi2'
    wifi_settings2['wireless']['mode'] = 'infrastructure'
    wifi_settings2['wireless']['auth_mode'] = 'wpa'
    wifi_settings2['wireless']['passphrase'] = 'secretpassword'
    network.edit_connection(connection, wifi_settings2)

    connection = network.get_connection(wifi_uuid)

    assert connection.get_id() == 'plinth_test_wifi_new'

    settings_connection = connection.get_setting_connection()
    assert settings_connection.get_interface_name() == 'wlan1'
    assert settings_connection.get_zone() == 'external'
    assert settings_connection.get_dns_over_tls().value_nick == 'opportunistic'
    assert not settings_connection.get_autoconnect()

    settings_wireless = connection.get_setting_wireless()
    assert settings_wireless.get_ssid().get_data() == b'plinthtestwifi2'
    assert settings_wireless.get_ssid().get_data().decode(
    ) == 'plinthtestwifi2'
    assert settings_wireless.get_mode() == 'infrastructure'

    wifi_sec = connection.get_setting_wireless_security()
    assert wifi_sec.get_key_mgmt() == 'wpa-psk'

    secrets = connection.get_secrets('802-11-wireless-security')
    assert secrets['802-11-wireless-security']['psk'] == 'secretpassword'


def test_ethernet_manual_ipv4_address(network, ethernet_uuid):
    """Check that we can manually set IPv4 address on ethernet."""
    connection = network.get_connection(ethernet_uuid)
    ethernet_settings2 = copy.deepcopy(ethernet_settings)
    ethernet_settings2['ipv4']['method'] = 'manual'
    ethernet_settings2['ipv4']['address'] = '169.254.0.1'
    ethernet_settings2['ipv4']['netmask'] = '255.255.254.0'
    ethernet_settings2['ipv4']['gateway'] = '169.254.0.254'
    ethernet_settings2['ipv4']['dns'] = '1.2.3.4'
    ethernet_settings2['ipv4']['second_dns'] = '1.2.3.5'
    network.edit_connection(connection, ethernet_settings2)

    connection = network.get_connection(ethernet_uuid)
    settings_ipv4 = connection.get_setting_ip4_config()
    assert settings_ipv4.get_method() == 'manual'

    address = settings_ipv4.get_address(0)
    assert address.get_address() == '169.254.0.1'
    assert address.get_prefix() == 23
    assert settings_ipv4.get_gateway() == '169.254.0.254'
    assert settings_ipv4.get_num_dns() == 2
    assert settings_ipv4.get_dns(0) == '1.2.3.4'
    assert settings_ipv4.get_dns(1) == '1.2.3.5'


def test_ethernet_manual_ipv6_address(network, ethernet_uuid):
    """Check that we can manually set IPv6 address on ethernet."""
    connection = network.get_connection(ethernet_uuid)
    ethernet_settings2 = copy.deepcopy(ethernet_settings)
    ethernet_settings2['ipv6']['method'] = 'manual'
    ethernet_settings2['ipv6']['address'] = '::ffff:169.254.0.1'
    ethernet_settings2['ipv6']['prefix'] = '63'
    ethernet_settings2['ipv6']['gateway'] = '::ffff:169.254.0.254'
    ethernet_settings2['ipv6']['dns'] = '::ffff:1.2.3.4'
    ethernet_settings2['ipv6']['second_dns'] = '::ffff:1.2.3.5'
    network.edit_connection(connection, ethernet_settings2)

    connection = network.get_connection(ethernet_uuid)
    settings_ipv6 = connection.get_setting_ip6_config()
    assert settings_ipv6.get_method() == 'manual'

    address = settings_ipv6.get_address(0)
    assert address.get_address() == '::ffff:169.254.0.1'
    assert address.get_prefix() == 63
    assert settings_ipv6.get_gateway() == '::ffff:169.254.0.254'
    assert settings_ipv6.get_num_dns() == 2
    assert settings_ipv6.get_dns(0) == '::ffff:1.2.3.4'
    assert settings_ipv6.get_dns(1) == '::ffff:1.2.3.5'


def test_wifi_manual_ipv4_address(network, wifi_uuid):
    """Check that we can manually set IPv4 address on wifi."""
    connection = network.get_connection(wifi_uuid)
    wifi_settings2 = copy.deepcopy(wifi_settings)
    wifi_settings2['ipv4']['method'] = 'manual'
    wifi_settings2['ipv4']['address'] = '169.254.0.2'
    wifi_settings2['ipv4']['netmask'] = '255.255.254.0'
    wifi_settings2['ipv4']['gateway'] = '169.254.0.254'
    wifi_settings2['ipv4']['dns'] = '1.2.3.4'
    wifi_settings2['ipv4']['second_dns'] = '1.2.3.5'
    wifi_settings2['wireless']['ssid'] = 'plinthtestwifi'
    wifi_settings2['wireless']['mode'] = 'adhoc'
    wifi_settings2['wireless']['auth_mode'] = 'open'
    network.edit_connection(connection, wifi_settings2)

    connection = network.get_connection(wifi_uuid)
    settings_ipv4 = connection.get_setting_ip4_config()
    assert settings_ipv4.get_method() == 'manual'

    address = settings_ipv4.get_address(0)
    assert address.get_address() == '169.254.0.2'
    assert address.get_prefix() == 23
    assert settings_ipv4.get_gateway() == '169.254.0.254'
    assert settings_ipv4.get_num_dns() == 2
    assert settings_ipv4.get_dns(0) == '1.2.3.4'
    assert settings_ipv4.get_dns(1) == '1.2.3.5'


def test_wifi_manual_ipv6_address(network, wifi_uuid):
    """Check that we can manually set IPv6 address on wifi."""
    connection = network.get_connection(wifi_uuid)
    wifi_settings2 = copy.deepcopy(wifi_settings)
    wifi_settings2['ipv6']['method'] = 'manual'
    wifi_settings2['ipv6']['address'] = '::ffff:169.254.0.2'
    wifi_settings2['ipv6']['prefix'] = 63
    wifi_settings2['ipv6']['gateway'] = '::ffff:169.254.0.254'
    wifi_settings2['ipv6']['dns'] = '::ffff:1.2.3.4'
    wifi_settings2['ipv6']['second_dns'] = '::ffff:1.2.3.5'
    wifi_settings2['wireless']['ssid'] = 'plinthtestwifi'
    wifi_settings2['wireless']['mode'] = 'adhoc'
    wifi_settings2['wireless']['auth_mode'] = 'open'
    network.edit_connection(connection, wifi_settings2)

    connection = network.get_connection(wifi_uuid)
    settings_ipv6 = connection.get_setting_ip6_config()
    assert settings_ipv6.get_method() == 'manual'

    address = settings_ipv6.get_address(0)
    assert address.get_address() == '::ffff:169.254.0.2'
    assert address.get_prefix() == 63
    assert settings_ipv6.get_gateway() == '::ffff:169.254.0.254'
    assert settings_ipv6.get_num_dns() == 2
    assert settings_ipv6.get_dns(0) == '::ffff:1.2.3.4'
    assert settings_ipv6.get_dns(1) == '::ffff:1.2.3.5'
