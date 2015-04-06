#!/usr/bin/python3
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
        connection = network.add_ethernet_connection(
            'plinth_test_eth', 'internal',
            'auto', '')
        cls.ethernet_uuid = connection['connection']['uuid']
        connection = network.add_wifi_connection(
            'plinth_test_wifi', 'external',
            'plinthtestwifi', 'adhoc', 'open', '',
            'auto', '')
        cls.wifi_uuid = connection['connection']['uuid']

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
            connection.GetSettings()['connection']['id'], 'plinth_test_eth')

        connection = network.get_connection(self.wifi_uuid)
        self.assertEqual(
            connection.GetSettings()['connection']['id'], 'plinth_test_wifi')

        self.assertRaises(network.ConnectionNotFound, network.get_connection,
                          'x-invalid-network-id')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_edit_ethernet_connection(self):
        """Check that we can update an ethernet connection."""
        connection = network.get_connection(self.ethernet_uuid)
        network.edit_ethernet_connection(
            connection, 'plinth_test_eth_new', 'external', 'manual',
            '169.254.0.1')

        connection = network.get_connection(self.ethernet_uuid)
        settings = connection.GetSettings()
        self.assertEqual(settings['connection']['id'], 'plinth_test_eth_new')
        self.assertEqual(settings['connection']['zone'], 'external')
        self.assertEqual(settings['ipv4']['method'], 'manual')
        self.assertEqual(settings['ipv4']['addresses'],
                         [['169.254.0.1', 24, '0.0.0.0']])

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_edit_wifi_connection(self):
        """Check that we can update a wifi connection."""
        connection = network.get_connection(self.wifi_uuid)
        network.edit_wifi_connection(
            connection, 'plinth_test_wifi_new', 'external',
            'plinthtestwifi2', 'infrastructure', 'wpa', 'secretpassword',
            'auto', '')

        connection = network.get_connection(self.wifi_uuid)
        settings = connection.GetSettings()
        self.assertEqual(settings['connection']['id'], 'plinth_test_wifi_new')
        self.assertEqual(settings['connection']['zone'], 'external')
        self.assertEqual(settings['802-11-wireless']['ssid'],
                         'plinthtestwifi2')
        self.assertEqual(settings['802-11-wireless']['mode'], 'infrastructure')
        self.assertEqual(settings['802-11-wireless-security']['key-mgmt'],
                         'wpa-psk')
        self.assertEqual(
            connection.GetSecrets()['802-11-wireless-security']['psk'],
            'secretpassword')


if __name__ == "__main__":
    unittest.main()
