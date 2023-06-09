# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for Tor module.
"""

from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError

from plinth.modules.tor import forms, utils


class TestTor:
    """Test cases for testing the Tor module."""

    @staticmethod
    @patch('plinth.app.App.get')
    @pytest.mark.usefixtures('needs_root', 'load_cfg')
    def test_get_status(_app_get):
        """Test that get_status does not raise any unhandled exceptions.

        This should work regardless of whether tor is installed, or
        /etc/tor/instances/plinth/torrc exists.
        """
        utils.get_status()


class TestTorForm:
    """Test whether Tor configration form works."""

    @staticmethod
    def test_bridge_validator():
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
        with pytest.raises(ValidationError):
            validator('  ')

        # Invalid IP address/port
        with pytest.raises(ValidationError):
            validator('73.237.165.384:9001')

        with pytest.raises(ValidationError):
            validator('73.237.165.184:90001')

        with pytest.raises(ValidationError):
            validator('[a2001:db8:85a3:8d3:1319:8a2e:370:7348]:443')

        with pytest.raises(ValidationError):
            validator('[2001:db8:85a3:8d3:1319:8a2e:370:7348]:90443')
