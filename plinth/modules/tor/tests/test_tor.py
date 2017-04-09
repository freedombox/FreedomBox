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

from django.core.exceptions import ValidationError
import os
import unittest

from plinth.modules.tor import utils
from plinth.modules.tor import forms

euid = os.geteuid()


class TestTor(unittest.TestCase):
    """Test cases for testing the tor module."""
    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_is_apt_transport_tor_enabled(self):
        """Test that is_apt_transport_tor_enabled does not raise any unhandled
        exceptions.
        """
        utils._is_apt_transport_tor_enabled()

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_get_status(self):
        """Test that get_status does not raise any unhandled exceptions.

        This should work regardless of whether tor is installed, or
        /etc/tor/torrc exists.
        """
        utils.get_status()


class TestTorForm(unittest.TestCase):
    """Test whether Tor configration form works."""
    def test_bridge_validator(self):
        """Test upstream bridges' form field validator."""
        validator = forms.bridges_validator

        # Just IP:port
        validator('73.237.165.184:9001')
        validator('73.237.165.184')
        validator('[2001:db8:85a3:8d3:1319:8a2e:370:7348]:443')
        validator('[2001:db8:85a3:8d3:1319:8a2e:370:7348]')

        # With fingerprint
        validator('73.237.165.184:9001 '
                  '0D04F10F497E68D2AF32375BB763EC3458A908C8')

        # With transport type
        validator('obfs4 73.237.165.184:9001 '
                  '0D04F10F497E68D2AF32375BB763EC3458A908C8')

        # With transport type and extra options
        validator('obfs4 10.1.1.1:30000 '
                  '0123456789ABCDEF0123456789ABCDEF01234567 '
                  'cert=A/b+1 iat-mode=0')

        # Leading, trailing spaces and empty lines
        validator('\n'
                  '  \n'
                  '73.237.165.184:9001 '
                  '0D04F10F497E68D2AF32375BB763EC3458A908C8'
                  '  \n'
                  '73.237.165.184:9001 '
                  '0D04F10F497E68D2AF32375BB763EC3458A908C8'
                  '  \n'
                  '\n')

        # Invalid number for parts
        self.assertRaises(ValidationError, validator, '  ')

        # Invalid IP address/port
        self.assertRaises(ValidationError, validator, '73.237.165.384:9001')
        self.assertRaises(ValidationError, validator, '73.237.165.184:90001')
        self.assertRaises(ValidationError, validator,
                          '[a2001:db8:85a3:8d3:1319:8a2e:370:7348]:443')
        self.assertRaises(ValidationError, validator,
                          '[2001:db8:85a3:8d3:1319:8a2e:370:7348]:90443')
