# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for Tor Proxy module.
"""

from unittest.mock import patch

import pytest

from plinth.modules.torproxy import utils


class TestTorProxy:
    """Test cases for testing the Tor Proxy module."""

    @staticmethod
    @pytest.mark.usefixtures('needs_root')
    def test_is_apt_transport_tor_enabled():
        """Test that is_apt_transport_tor_enabled does not raise any unhandled
        exceptions.
        """
        utils.is_apt_transport_tor_enabled()

    @staticmethod
    @patch('plinth.app.App.get')
    @pytest.mark.usefixtures('needs_root', 'load_cfg')
    def test_get_status(_app_get):
        """Test that get_status does not raise any unhandled exceptions.

        This should work regardless of whether tor is installed, or
        /etc/tor/instances/fbxproxy/torrc exists.
        """
        utils.get_status()
