#
# This file is part of FreedomBox.
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
Test module for clients module.
"""

import unittest

from plinth import clients
from plinth.modules.deluge.manifest import clients as deluge_clients
from plinth.modules.infinoted.manifest import clients as infinoted_clients
from plinth.modules.quassel.manifest import clients as quassel_clients
from plinth.modules.syncthing.manifest import clients as syncthing_clients
from plinth.modules.tor.manifest import clients as tor_clients


class TestClients(unittest.TestCase):
    """Test utilities provided by clients module."""

    def test_of_type_web(self):
        """Test filtering clients of type web."""
        self.assertTrue(clients.of_type(syncthing_clients, 'web'))
        self.assertFalse(clients.of_type(quassel_clients, 'web'))

    def test_of_type_mobile(self):
        """Test filtering clients of type mobile."""
        self.assertTrue(clients.of_type(syncthing_clients, 'mobile'))
        self.assertFalse(clients.of_type(infinoted_clients, 'mobile'))

    def test_of_type_desktop(self):
        """Test filtering clients of type desktop."""
        self.assertTrue(clients.of_type(syncthing_clients, 'desktop'))
        self.assertFalse(clients.of_type(deluge_clients, 'desktop'))

    def test_of_type_package(self):
        """Test filtering clients of type package."""
        self.assertTrue(clients.of_type(syncthing_clients, 'package'))
        self.assertFalse(clients.of_type(tor_clients, 'package'))
