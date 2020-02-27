# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for clients module.
"""

from plinth import clients
from plinth.modules.deluge.manifest import clients as deluge_clients
from plinth.modules.infinoted.manifest import clients as infinoted_clients
from plinth.modules.quassel.manifest import clients as quassel_clients
from plinth.modules.syncthing.manifest import clients as syncthing_clients
from plinth.modules.tor.manifest import clients as tor_clients


def test_of_type_web():
    """Test filtering clients of type web."""
    assert clients.of_type(syncthing_clients, 'web')
    assert not clients.of_type(quassel_clients, 'web')


def test_of_type_mobile():
    """Test filtering clients of type mobile."""
    assert clients.of_type(syncthing_clients, 'mobile')
    assert not clients.of_type(infinoted_clients, 'mobile')


def test_of_type_desktop():
    """Test filtering clients of type desktop."""
    assert clients.of_type(syncthing_clients, 'desktop')
    assert not clients.of_type(deluge_clients, 'desktop')


def test_of_type_package():
    """Test filtering clients of type package."""
    assert clients.of_type(syncthing_clients, 'package')
    assert not clients.of_type(tor_clients, 'package')
