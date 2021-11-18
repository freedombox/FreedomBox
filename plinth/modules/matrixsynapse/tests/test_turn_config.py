# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Matrix Synapse STUN/TURN configuration.
"""

from unittest.mock import patch

import pytest

from plinth.modules import matrixsynapse
from plinth.modules.coturn.components import TurnConfiguration

actions_name = 'matrixsynapse'


@pytest.fixture(name='managed_turn_conf_file')
def fixture_managed_turn_conf_file(tmp_path):
    """Returns a dummy TURN configuration file."""
    conf_file = tmp_path / 'freedombox-turn.yaml'
    return str(conf_file)


@pytest.fixture(name='overridden_turn_conf_file')
def fixture_overridden_turn_conf_file(tmp_path):
    """Returns a dummy TURN configuration file."""
    conf_file = tmp_path / 'turn.yaml'
    return str(conf_file)


@pytest.fixture(autouse=True)
def fixture_set_paths(actions_module, capsys, managed_turn_conf_file,
                      overridden_turn_conf_file):
    """Run actions with custom root path."""
    actions_module.TURN_CONF_PATH = managed_turn_conf_file
    actions_module.OVERRIDDEN_TURN_CONF_PATH = overridden_turn_conf_file
    with patch('plinth.action_utils.service_try_restart'):
        yield


@pytest.fixture(name='test_configuration', autouse=True)
def fixture_test_configuration(call_action, managed_turn_conf_file,
                               overridden_turn_conf_file):
    """Use a separate Matrix Synapse configuration for tests.

    Overrides TURN configuration files and patches actions.superuser_run
    with the fixture call_action
    """
    with (patch('plinth.modules.matrixsynapse.TURN_CONF_PATH',
                managed_turn_conf_file),
          patch('plinth.modules.matrixsynapse.OVERRIDDEN_TURN_CONF_PATH',
                overridden_turn_conf_file),
          patch('plinth.modules.matrixsynapse.is_setup', return_value=True),
          patch('plinth.actions.superuser_run', call_action),
          patch('plinth.modules.matrixsynapse.app') as app):
        app.needs_setup.return_value = False
        yield


coturn_configuration = TurnConfiguration(
    'freedombox.local', [],
    'aiP02OAGyOlj6WGuCyqj7iaOsbkC7BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51')

overridden_configuration = TurnConfiguration(
    'public.coturn.site', [],
    'BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51aiP02OAGyOlj6WGuCyqj7iaOsbkC7')

updated_coturn_configuration = TurnConfiguration(
    'my.freedombox.rocks', [],
    'aiP02OsbkC7BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51AGyOlj6WGuCyqj7iaO')


def _set_managed_configuration(monkeypatch, config=coturn_configuration):
    monkeypatch.setattr('sys.stdin', config.to_json())
    matrixsynapse.update_turn_configuration(config)


def _set_overridden_configuration(monkeypatch,
                                  config=overridden_configuration):
    monkeypatch.setattr('sys.stdin', config.to_json())
    matrixsynapse.update_turn_configuration(config, managed=False)


def _assert_conf(expected_configuration, expected_managed):
    """Assert that matrix synapse TURN configuration is as expected."""
    config, managed = matrixsynapse.get_turn_configuration()
    assert config.uris == expected_configuration.uris
    assert config.shared_secret == expected_configuration.shared_secret
    assert managed == expected_managed


def test_managed_turn_server_configuration(monkeypatch):
    """Test setting and getting managed TURN server configuration."""
    _set_managed_configuration(monkeypatch)
    _assert_conf(coturn_configuration, True)


def test_overridden_turn_server_configuration(monkeypatch):
    """Test setting and getting overridden TURN sever configuration."""
    _set_overridden_configuration(monkeypatch)
    _assert_conf(overridden_configuration, False)


def test_revert_to_managed_turn_server_configuration(monkeypatch):
    """Test setting and getting overridden TURN sever configuration."""
    # Had to do all 3 operations because all fixtures were function-scoped
    _set_managed_configuration(monkeypatch)
    _set_overridden_configuration(monkeypatch)
    _set_overridden_configuration(monkeypatch, TurnConfiguration())
    _assert_conf(coturn_configuration, True)


def test_coturn_configuration_update_after_admin_override(monkeypatch):
    """Test that overridden conf prevails even if managed conf is updated."""
    _set_managed_configuration(monkeypatch)
    _set_overridden_configuration(monkeypatch)
    _set_managed_configuration(monkeypatch, updated_coturn_configuration)
    _assert_conf(overridden_configuration, False)
