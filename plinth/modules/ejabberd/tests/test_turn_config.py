# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for ejabberd STUN/TURN configuration.
"""

import pathlib
import shutil
from unittest.mock import MagicMock, patch

import pytest

from plinth.modules import ejabberd
from plinth.modules.coturn.components import TurnConfiguration

managed_configuration = TurnConfiguration(
    'freedombox.local', [],
    'aiP02OAGyOlj6WGuCyqj7iaOsbkC7BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51')

overridden_configuration = TurnConfiguration(
    'public.coturn.site', [],
    'BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51aiP02OAGyOlj6WGuCyqj7iaOsbkC7')

actions_name = 'ejabberd'

current_directory = pathlib.Path(__file__).parent


@pytest.fixture(name='conf_file')
def fixture_conf_file(tmp_path):
    """Uses a dummy configuration file."""
    settings_file_name = 'ejabberd.yml'
    conf_file = tmp_path / settings_file_name
    conf_file.touch()
    shutil.copyfile(str(current_directory / 'data' / 'ejabberd.yml.example'),
                    str(conf_file))
    return str(conf_file)


@pytest.fixture(name='managed_file')
def fixture_managed_file(tmp_path):
    """Uses a dummy managed file."""
    file_name = 'freedombox_managed_coturn'
    fil = tmp_path / file_name
    return str(fil)


@pytest.fixture(autouse=True)
def fixture_set_configuration_paths(actions_module, conf_file, managed_file):
    """Setup configuration file paths in action module."""
    actions_module.EJABBERD_CONFIG = conf_file
    actions_module.EJABBERD_MANAGED_COTURN = managed_file


@pytest.fixture(name='test_configuration', autouse=True)
def fixture_test_configuration(call_action, conf_file):
    """Use a separate ejabberd configuration for tests.

    Patches actions.superuser_run with the fixture call_action.
    The module state is patched to be 'up-to-date'.
    """
    with patch('plinth.actions.superuser_run', call_action):
        helper = MagicMock()
        helper.get_state.return_value = 'up-to-date'
        ejabberd.setup_helper = helper
        yield


def _set_turn_configuration(monkeypatch, config=managed_configuration,
                            managed=True):
    monkeypatch.setattr('sys.stdin', config.to_json())
    with patch('plinth.action_utils.service_is_running', return_value=False):
        ejabberd.update_turn_configuration(config, managed=managed)


def _assert_conf(expected_configuration, expected_managed):
    """Assert that ejabberd TURN configuration is as expected."""
    config, managed = ejabberd.get_turn_configuration()
    assert config.uris == expected_configuration.uris
    assert config.shared_secret == expected_configuration.shared_secret
    assert managed == expected_managed


def test_managed_turn_server_configuration(monkeypatch):
    _set_turn_configuration(monkeypatch)
    _assert_conf(managed_configuration, True)


def test_overridden_turn_server_configuration(monkeypatch):
    _set_turn_configuration(monkeypatch, overridden_configuration, False)
    _assert_conf(overridden_configuration, False)


def test_remove_turn_configuration(monkeypatch):
    _set_turn_configuration(monkeypatch)
    _set_turn_configuration(monkeypatch, TurnConfiguration(), False)
    _assert_conf(TurnConfiguration(), False)
