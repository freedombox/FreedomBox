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
Test module for network configuration utilities.
"""

import copy
import os
import time
import unittest


euid = os.geteuid()
if euid == 0:
    from plinth import network

ethernet_settings = {
    'common': {
        'type': '802-3-ethernet',
        'name': 'plinth_test_eth',
        'interface': 'eth0',
        'zone': 'internal',
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


class TestNetwork(unittest.TestCase):
    """Verify that the network module performs as expected."""

    ethernet_uuid = None
    wifi_uuid = None
    pppoe_uuid = None

    @classmethod
    def setUp(cls):
        cls.ethernet_uuid = network.add_connection(ethernet_settings)
        cls.wifi_uuid = network.add_connection(wifi_settings)
        cls.pppoe_uuid = network.add_connection(pppoe_settings)
        # XXX: Handle this properly by waiting for asynchronous add_connection
        # to complete.
        time.sleep(0.1)

    @classmethod
    def tearDown(cls):
        network.delete_connection(cls.ethernet_uuid)
        network.delete_connection(cls.wifi_uuid)
        network.delete_connection(cls.pppoe_uuid)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_get_connection_list(self):
        """Check that we can get a list of available connections."""
        connections = network.get_connection_list()

        self.assertTrue('plinth_test_eth' in [x['name'] for x in connections])
        self.assertTrue('plinth_test_wifi' in [x['name'] for x in connections])
        self.assertTrue('plinth_test_pppoe' in
                        [x['name'] for x in connections])

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_get_connection(self):
        """Check that we can get a connection by name."""
        connection = network.get_connection(self.ethernet_uuid)
        self.assertEqual(
            connection.get_id(), 'plinth_test_eth')

        connection = network.get_connection(self.wifi_uuid)
        self.assertEqual(
            connection.get_id(), 'plinth_test_wifi')

        self.assertRaises(network.ConnectionNotFound, network.get_connection,
                          'x-invalid-network-id')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_edit_ethernet_connection(self):
        """Check that we can update an ethernet connection."""
        connection = network.get_connection(self.ethernet_uuid)
        ethernet_settings2 = copy.deepcopy(ethernet_settings)
        ethernet_settings2['common']['name'] = 'plinth_test_eth_new'
        ethernet_settings2['common']['interface'] = 'eth1'
        ethernet_settings2['common']['zone'] = 'external'
        ethernet_settings2['ipv4']['method'] = 'auto'
        network.edit_connection(connection, ethernet_settings2)

        connection = network.get_connection(self.ethernet_uuid)
        self.assertEqual(connection.get_id(), 'plinth_test_eth_new')

        settings_connection = connection.get_setting_connection()
        self.assertEqual(settings_connection.get_interface_name(), 'eth1')
        self.assertEqual(settings_connection.get_zone(), 'external')

        settings_ipv4 = connection.get_setting_ip4_config()
        self.assertEqual(settings_ipv4.get_method(), 'auto')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_edit_pppoe_connection(self):
        """Check that we can update a PPPoE connection."""
        connection = network.get_connection(self.ethernet_uuid)
        pppoe_settings2 = copy.deepcopy(pppoe_settings)
        pppoe_settings2['common']['name'] = 'plinth_test_pppoe_new'
        pppoe_settings2['common']['interface'] = 'eth2'
        pppoe_settings2['common']['zone'] = 'external'
        pppoe_settings2['pppoe']['username'] = 'x-user-new'
        pppoe_settings2['pppoe']['password'] = 'x-password-new'
        network.edit_connection(connection, pppoe_settings2)

        connection = network.get_connection(self.ethernet_uuid)
        self.assertEqual(connection.get_id(), 'plinth_test_pppoe_new')

        settings_connection = connection.get_setting_connection()
        self.assertEqual(settings_connection.get_interface_name(), 'eth2')
        self.assertEqual(settings_connection.get_zone(), 'external')

        settings_pppoe = connection.get_setting_pppoe()
        self.assertEqual(settings_pppoe.get_username(), 'x-user-new')
        secrets = connection.get_secrets('pppoe')
        self.assertEqual(secrets['pppoe']['password'], 'x-password-new')

        settings_ppp = connection.get_setting_ppp()
        self.assertEqual(settings_ppp.get_lcp_echo_failure(), 5)
        self.assertEqual(settings_ppp.get_lcp_echo_interval(), 30)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_edit_wifi_connection(self):
        """Check that we can update a wifi connection."""
        connection = network.get_connection(self.wifi_uuid)
        wifi_settings2 = copy.deepcopy(wifi_settings)
        wifi_settings2['common']['name'] = 'plinth_test_wifi_new'
        wifi_settings2['common']['interface'] = 'wlan1'
        wifi_settings2['common']['zone'] = 'external'
        wifi_settings2['ipv4']['method'] = 'auto'
        wifi_settings2['wireless']['ssid'] = 'plinthtestwifi2'
        wifi_settings2['wireless']['mode'] = 'infrastructure'
        wifi_settings2['wireless']['auth_mode'] = 'wpa'
        wifi_settings2['wireless']['passphrase'] = 'secretpassword'
        network.edit_connection(connection, wifi_settings2)

        connection = network.get_connection(self.wifi_uuid)

        self.assertEqual(connection.get_id(), 'plinth_test_wifi_new')

        settings_connection = connection.get_setting_connection()
        self.assertEqual(settings_connection.get_interface_name(), 'wlan1')
        self.assertEqual(settings_connection.get_zone(), 'external')

        settings_wireless = connection.get_setting_wireless()
        self.assertEqual(settings_wireless.get_ssid().get_data(),
                         b'plinthtestwifi2')
        self.assertEqual(settings_wireless.get_mode(), 'infrastructure')

        wifi_sec = connection.get_setting_wireless_security()
        self.assertEqual(wifi_sec.get_key_mgmt(), 'wpa-psk')

        secrets = connection.get_secrets('802-11-wireless-security')
        self.assertEqual(
            secrets['802-11-wireless-security']['psk'],
            'secretpassword')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_ethernet_manual_ipv4_address(self):
        """Check that we can manually set IPv4 address on ethernet."""
        connection = network.get_connection(self.ethernet_uuid)
        ethernet_settings2 = copy.deepcopy(ethernet_settings)
        ethernet_settings2['ipv4']['method'] = 'manual'
        ethernet_settings2['ipv4']['address'] = '169.254.0.1'
        ethernet_settings2['ipv4']['netmask'] = '255.255.254.0'
        ethernet_settings2['ipv4']['gateway'] = '169.254.0.254'
        ethernet_settings2['ipv4']['dns'] = '1.2.3.4'
        ethernet_settings2['ipv4']['second_dns'] = '1.2.3.5'
        network.edit_connection(connection, ethernet_settings2)

        connection = network.get_connection(self.ethernet_uuid)
        settings_ipv4 = connection.get_setting_ip4_config()
        self.assertEqual(settings_ipv4.get_method(), 'manual')

        address = settings_ipv4.get_address(0)
        self.assertEqual(address.get_address(), '169.254.0.1')
        self.assertEqual(address.get_prefix(), 23)
        self.assertEqual(settings_ipv4.get_gateway(), '169.254.0.254')
        self.assertEqual(settings_ipv4.get_num_dns(), 2)
        self.assertEqual(settings_ipv4.get_dns(0), '1.2.3.4')
        self.assertEqual(settings_ipv4.get_dns(1), '1.2.3.5')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_ethernet_manual_ipv6_address(self):
        """Check that we can manually set IPv6 address on ethernet."""
        connection = network.get_connection(self.ethernet_uuid)
        ethernet_settings2 = copy.deepcopy(ethernet_settings)
        ethernet_settings2['ipv6']['method'] = 'manual'
        ethernet_settings2['ipv6']['address'] = '::ffff:169.254.0.1'
        ethernet_settings2['ipv6']['prefix'] = '63'
        ethernet_settings2['ipv6']['gateway'] = '::ffff:169.254.0.254'
        ethernet_settings2['ipv6']['dns'] = '::ffff:1.2.3.4'
        ethernet_settings2['ipv6']['second_dns'] = '::ffff:1.2.3.5'
        network.edit_connection(connection, ethernet_settings2)

        connection = network.get_connection(self.ethernet_uuid)
        settings_ipv6 = connection.get_setting_ip6_config()
        self.assertEqual(settings_ipv6.get_method(), 'manual')

        address = settings_ipv6.get_address(0)
        self.assertEqual(address.get_address(), '::ffff:169.254.0.1')
        self.assertEqual(address.get_prefix(), 63)
        self.assertEqual(settings_ipv6.get_gateway(), '::ffff:169.254.0.254')
        self.assertEqual(settings_ipv6.get_num_dns(), 2)
        self.assertEqual(settings_ipv6.get_dns(0), '::ffff:1.2.3.4')
        self.assertEqual(settings_ipv6.get_dns(1), '::ffff:1.2.3.5')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_wifi_manual_ipv4_address(self):
        """Check that we can manually set IPv4 address on wifi."""
        connection = network.get_connection(self.wifi_uuid)
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

        connection = network.get_connection(self.wifi_uuid)
        settings_ipv4 = connection.get_setting_ip4_config()
        self.assertEqual(settings_ipv4.get_method(), 'manual')

        address = settings_ipv4.get_address(0)
        self.assertEqual(address.get_address(), '169.254.0.2')
        self.assertEqual(address.get_prefix(), 23)
        self.assertEqual(settings_ipv4.get_gateway(), '169.254.0.254')
        self.assertEqual(settings_ipv4.get_num_dns(), 2)
        self.assertEqual(settings_ipv4.get_dns(0), '1.2.3.4')
        self.assertEqual(settings_ipv4.get_dns(1), '1.2.3.5')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_wifi_manual_ipv6_address(self):
        """Check that we can manually set IPv6 address on wifi."""
        connection = network.get_connection(self.wifi_uuid)
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

        connection = network.get_connection(self.wifi_uuid)
        settings_ipv6 = connection.get_setting_ip6_config()
        self.assertEqual(settings_ipv6.get_method(), 'manual')

        address = settings_ipv6.get_address(0)
        self.assertEqual(address.get_address(), '::ffff:169.254.0.2')
        self.assertEqual(address.get_prefix(), 63)
        self.assertEqual(settings_ipv6.get_gateway(), '::ffff:169.254.0.254')
        self.assertEqual(settings_ipv6.get_num_dns(), 2)
        self.assertEqual(settings_ipv6.get_dns(0), '::ffff:1.2.3.4')
        self.assertEqual(settings_ipv6.get_dns(1), '::ffff:1.2.3.5')
