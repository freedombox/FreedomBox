# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for the Coturn app component.
"""

import json
from unittest.mock import call, patch

import pytest

from plinth.utils import random_string

from .. import notify_configuration_change
from ..components import (TurnConfiguration, TurnConsumer,
                          TurnTimeLimitedConsumer, UserTurnConfiguration)


@pytest.fixture(name='turn_configuration')
def fixture_turn_configuration():
    """Return test Coturn configuration."""
    return TurnConfiguration('test-domain.example', [], random_string(64))


@pytest.fixture(name='empty_component_list', autouse=True)
def fixture_empty_component_list():
    """Remove all entries in component list before starting a test."""
    TurnConsumer._all = {}


def test_turn_configuration_init():
    """Test creating configuration object."""
    config = TurnConfiguration('test-domain.example', [], 'test-shared-secret')
    assert config.domain == 'test-domain.example'
    assert config.shared_secret == 'test-shared-secret'
    assert config.uris == [
        'stun:test-domain.example:3478',
        'turn:test-domain.example:3478?transport=tcp',
        'turn:test-domain.example:3478?transport=udp',
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

    config = UserTurnConfiguration('test-domain.example',
                                   ['test-uri1', 'test-uri2'], None,
                                   'test-username', 'test-credential')
    assert config.domain == 'test-domain.example'
    assert config.uris == ['test-uri1', 'test-uri2']
    assert config.shared_secret is None
    assert config.username == 'test-username'
    assert config.credential == 'test-credential'


def test_turn_configuration_to_json():
    """Test exporting configuration to JSON."""
    config = TurnConfiguration('test-domain.example', [], 'test-shared-secret')
    assert json.loads(config.to_json()) == {
        'domain': 'test-domain.example',
        'uris': [
            'stun:test-domain.example:3478',
            'turn:test-domain.example:3478?transport=tcp',
            'turn:test-domain.example:3478?transport=udp',
        ],
        'shared_secret': 'test-shared-secret'
    }


def test_turn_configuration_validate_turn_uris():
    """Test validation method to check for STUN/TURN URIs."""
    valid_uris = [
        'stun:test-domain.example:3478',
        'turn:test-domain.example:3478?transport=tcp',
        'turn:test-domain.example:3478?transport=udp',
    ]
    invalid_uris = [
        'x-invalid-uri',
        'stun:',
        'stun:domain-port-missing.example',
        'stun:testing.example:1234invalid-append',
        'turn:testing.example:1234',
        'turn:testing.example:1234?invalid-param=value',
        'turn:testing.example:1234?transport=invalid-value',
        'turn:testing.example:1234?transport=tcp-invalid-append',
    ]
    assert TurnConfiguration().validate_turn_uris(valid_uris)
    for uri in invalid_uris:
        assert not TurnConfiguration().validate_turn_uris([uri])


def test_component_init_and_list():
    """Test initializing and listing all the components."""
    component1 = TurnConsumer('component1')
    component2 = TurnConsumer('component2')
    component3 = TurnTimeLimitedConsumer('component3')
    assert component1.component_id == 'component1'
    assert [component1, component2, component3] == list(TurnConsumer.list())


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


@patch('plinth.modules.coturn.get_config')
def test_get_user_configuration(get_config, turn_configuration):
    """Test coturn user configuration retrieval using component."""
    get_config.return_value = turn_configuration
    component = TurnTimeLimitedConsumer('component')
    user_config = component.get_configuration()
    assert user_config.domain == turn_configuration.domain
    assert user_config.uris == turn_configuration.uris
    assert user_config.shared_secret is None
    assert user_config.username is not None
    assert user_config.credential is not None
