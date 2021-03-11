# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for the Coturn app component.
"""

from unittest.mock import call, patch

import pytest

from plinth.utils import random_string

from .. import notify_configuration_change
from ..components import TurnConfiguration, TurnConsumer


@pytest.fixture(name='turn_configuration')
def fixture_turn_configuration():
    """Return test Coturn configuration."""
    return TurnConfiguration('test-domain.example', [], random_string(64))


@pytest.fixture(name='empty_component_list', autouse=True)
def fixture_empty_component_list():
    """Remove all entries in component list before starting a test."""
    TurnConsumer._all = {}


def test_configuration_init():
    """Test creating configuration object."""
    config = TurnConfiguration('test-domain.example', [], 'test-shared-secret')
    assert config.domain == 'test-domain.example'
    assert config.shared_secret == 'test-shared-secret'
    assert config.uris == [
        "stun:test-domain.example:3478?transport=tcp",
        "stun:test-domain.example:3478?transport=udp",
        "turn:test-domain.example:3478?transport=tcp",
        "turn:test-domain.example:3478?transport=udp",
    ]

    config = TurnConfiguration(None, ['test-uri1', 'test-uri2'],
                               'test-shared-secret')
    assert config.domain is None
    assert config.uris == ['test-uri1', 'test-uri2']

    config = TurnConfiguration('test-domain.example',
                               ['test-uri1', 'test-uri2'],
                               'test-shared-secret')
    assert config.domain == 'test-domain.example'
    assert config.uris == ['test-uri1', 'test-uri2']


def test_component_init_and_list():
    """Test initializing and listing all the components."""
    component1 = TurnConsumer('component1')
    component2 = TurnConsumer('component2')
    assert component1.component_id == 'component1'
    assert [component1, component2] == list(TurnConsumer.list())


@patch('plinth.modules.coturn.get_config')
def test_notify_on_configuration_changed(get_config, turn_configuration):
    """Test configuration change notifications."""
    component = TurnConsumer('component')
    get_config.return_value = turn_configuration
    with patch.object(component, 'on_config_change') as mock_method:
        notify_configuration_change()
        mock_method.assert_has_calls([call(turn_configuration)])


@patch('plinth.modules.coturn.get_config')
def test_get_configuration(get_config, turn_configuration):
    """Test coturn configuration retrieval using component."""
    get_config.return_value = turn_configuration
    component = TurnConsumer('component')
    assert component.get_configuration() == turn_configuration
