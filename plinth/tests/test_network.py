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

import os
import unittest


euid = os.geteuid()
if euid == 0:
    from plinth import network


class TestNetwork(unittest.TestCase):
    """Verify that the network module performs as expected."""

    ethernet_uuid = None
    wifi_uuid = None

    @classmethod
    def setUp(cls):
        cls.ethernet_uuid = network.add_ethernet_connection(
            'plinth_test_eth', 'eth0', 'internal',
            'auto', '')
        cls.wifi_uuid = network.add_wifi_connection(
            'plinth_test_wifi', 'wlan0', 'external',
            'plinthtestwifi', 'adhoc', 'open', '',
            'auto', '')

    @classmethod
    def tearDown(cls):
        network.delete_connection(cls.ethernet_uuid)
        network.delete_connection(cls.wifi_uuid)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_get_connection_list(self):
        """Check that we can get a list of available connections."""
        connections = network.get_connection_list()

        self.assertTrue('plinth_test_eth' in [x['name'] for x in connections])
        self.assertTrue('plinth_test_wifi' in [x['name'] for x in connections])

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
        network.edit_ethernet_connection(
            connection, 'plinth_test_eth_new', 'eth0', 'external', 'auto', '')

        connection = network.get_connection(self.ethernet_uuid)
        self.assertEqual(connection.get_id(), 'plinth_test_eth_new')

        settings_connection = connection.get_setting_connection()
        self.assertEqual(settings_connection.get_zone(), 'external')

        settings_ipv4 = connection.get_setting_ip4_config()
        self.assertEqual(settings_ipv4.get_method(), 'auto')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_edit_wifi_connection(self):
        """Check that we can update a wifi connection."""
        connection = network.get_connection(self.wifi_uuid)
        network.edit_wifi_connection(
            connection, 'plinth_test_wifi_new', 'wlan0', 'external',
            'plinthtestwifi2', 'infrastructure', 'wpa', 'secretpassword',
            'auto', '')

        connection = network.get_connection(self.wifi_uuid)

        self.assertEqual(connection.get_id(), 'plinth_test_wifi_new')

        settings_connection = connection.get_setting_connection()
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
        network.edit_ethernet_connection(
            connection, 'plinth_test_eth_new', 'eth0', 'external', 'manual',
            '169.254.0.1')

        connection = network.get_connection(self.ethernet_uuid)
        settings_ipv4 = connection.get_setting_ip4_config()
        self.assertEqual(settings_ipv4.get_method(), 'manual')

        address = settings_ipv4.get_address(0)
        self.assertEqual(address.get_address(), '169.254.0.1')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_wifi_manual_ipv4_address(self):
        """Check that we can manually set IPv4 address on wifi."""
        connection = network.get_connection(self.wifi_uuid)
        network.edit_wifi_connection(
            connection, 'plinth_test_wifi_new', 'wlan0', 'external',
            'plinthtestwifi', 'adhoc', 'open', '',
            'manual', '169.254.0.2')

        connection = network.get_connection(self.wifi_uuid)
        settings_ipv4 = connection.get_setting_ip4_config()
        self.assertEqual(settings_ipv4.get_method(), 'manual')

        address = settings_ipv4.get_address(0)
        self.assertEqual(address.get_address(), '169.254.0.2')
