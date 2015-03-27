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

import unittest

from plinth import network


class TestNetwork(unittest.TestCase):
    """Verify that the network module performs as expected."""

    @classmethod
    def setUpClass(cls):
        network.add_ethernet_connection(
            'plinth_test_eth', 'internal',
            'auto', '')
        network.add_wifi_connection(
            'plinth_test_wifi', 'external',
            'plinthtestwifi', 'adhoc', 'open', '',
            'auto', '')

    @classmethod
    def tearDownClass(cls):
        network.delete_connection('plinth_test_eth')
        network.delete_connection('plinth_test_wifi')

    def test_get_connection_list(self):
        """Check that we can get a list of available connections."""
        connections = network.get_connection_list()

        self.assertTrue('plinth_test_eth' in [x['name'] for x in connections])
        self.assertTrue('plinth_test_wifi' in [x['name'] for x in connections])

    def test_get_connection(self):
        """Check that we can get a connection by name."""
        conn = network.get_connection('plinth_test_eth')
        self.assertEqual(
            conn.GetSettings()['connection']['id'], 'plinth_test_eth')

        conn = network.get_connection('plinth_test_wifi')

        self.assertEqual(
            conn.GetSettings()['connection']['id'], 'plinth_test_wifi')

    def test_edit_ethernet_connection(self):
        """Check that we can update an ethernet connection."""
        conn = network.get_connection('plinth_test_eth')
        network.edit_ethernet_connection(
            conn, 'plinth_test_eth', 'external', 'manual', '169.254.0.1')
        conn = network.get_connection('plinth_test_eth')

        self.assertEqual(conn.GetSettings()['connection']['zone'], 'external')
        self.assertEqual(conn.GetSettings()['ipv4']['method'], 'manual')

    def test_edit_wifi_connection(self):
        """Check that we can update a wifi connection."""
        conn = network.get_connection('plinth_test_wifi')
        network.edit_wifi_connection(
            conn, 'plinth_test_wifi', 'external',
            'plinthtestwifi2', 'infrastructure', 'wpa', 'secretpassword',
            'auto', '')
        conn = network.get_connection('plinth_test_wifi')

        self.assertEqual(conn.GetSettings()['connection']['zone'], 'external')
        self.assertEqual(
            conn.GetSettings()['802-11-wireless']['ssid'], 'plinthtestwifi2')
        self.assertEqual(
            conn.GetSettings()['802-11-wireless']['mode'], 'infrastructure')
        self.assertEqual(
            conn.GetSettings()['802-11-wireless-security']['key-mgmt'],
            'wpa-psk')
        self.assertEqual(
            conn.GetSecrets()['802-11-wireless-security']['psk'],
            'secretpassword')

if __name__ == "__main__":
    unittest.main()
