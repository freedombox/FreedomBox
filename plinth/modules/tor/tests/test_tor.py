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
Tests for Tor module.
"""

import os
import unittest

from plinth.modules.tor import is_apt_transport_tor_enabled, get_hs, get_status

euid = os.geteuid()


class TestTor(unittest.TestCase):
    """Test cases for testing the tor module."""
    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_is_apt_transport_tor_enabled(self):
        """Test that is_apt_transport_tor_enabled does not raise any unhandled
        exceptions.
        """
        is_apt_transport_tor_enabled()

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_get_hs(self):
        """Test that get_hs does not raise any unhandled exceptions.

        This should work regardless of whether tor is installed, or
        /etc/tor/torrc exists.
        """
        get_hs()

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_get_status(self):
        """Test that get_status does not raise any unhandled exceptions.

        This should work regardless of whether tor is installed, or
        /etc/tor/torrc exists.
        """
        get_status()
