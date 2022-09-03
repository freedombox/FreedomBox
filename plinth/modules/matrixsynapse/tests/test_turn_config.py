# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Matrix Synapse STUN/TURN configuration.
"""

from unittest.mock import patch, Mock

import pytest

from plinth.modules import matrixsynapse
from plinth.modules.coturn.components import TurnConfiguration
from plinth.modules.matrixsynapse import privileged

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.modules.matrixsynapse.privileged']


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
def fixture_set_paths(managed_turn_conf_file, overridden_turn_conf_file):
    """Run actions with custom root path."""
    privileged.TURN_CONF_PATH = managed_turn_conf_file
    privileged.OVERRIDDEN_TURN_CONF_PATH = overridden_turn_conf_file
    with patch('plinth.privileged.service.try_restart'):
        yield


@pytest.fixture(name='test_configuration', autouse=True)
def fixture_test_configuration(managed_turn_conf_file,
                               overridden_turn_conf_file):
    """Use a separate Matrix Synapse configuration for tests.

    Overrides TURN configuration files.
    """
    matrixsynapse = 'plinth.modules.matrixsynapse'
    with (patch(f'{matrixsynapse}.privileged.TURN_CONF_PATH',
                managed_turn_conf_file),
          patch(f'{matrixsynapse}.privileged.OVERRIDDEN_TURN_CONF_PATH',
                overridden_turn_conf_file),
          patch(f'{matrixsynapse}.is_setup', return_value=True),
          patch('plinth.app.App.get') as app_get):
        app = Mock()
        app_get.return_value = app
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


def _set_managed_configuration(config=coturn_configuration):
    matrixsynapse.update_turn_configuration(config)


def _set_overridden_configuration(
                                  config=overridden_configuration):
    matrixsynapse.update_turn_configuration(config, managed=False)


def _assert_conf(expected_configuration, expected_managed):
    """Assert that matrix synapse TURN configuration is as expected."""
    config, managed = matrixsynapse.get_turn_configuration()
    assert config.uris == expected_configuration.uris
    assert config.shared_secret == expected_configuration.shared_secret
    assert managed == expected_managed


def test_managed_turn_server_configuration():
    """Test setting and getting managed TURN server configuration."""
    _set_managed_configuration()
    _assert_conf(coturn_configuration, True)


def test_overridden_turn_server_configuration():
    """Test setting and getting overridden TURN sever configuration."""
    _set_overridden_configuration()
    _assert_conf(overridden_configuration, False)


def test_revert_to_managed_turn_server_configuration():
    """Test setting and getting overridden TURN sever configuration."""
    # Had to do all 3 operations because all fixtures were function-scoped
    _set_managed_configuration()
    _set_overridden_configuration()
    _set_overridden_configuration(TurnConfiguration())
    _assert_conf(coturn_configuration, True)


def test_coturn_configuration_update_after_admin_override():
    """Test that overridden conf prevails even if managed conf is updated."""
    _set_managed_configuration()
    _set_overridden_configuration()
    _set_managed_configuration(updated_coturn_configuration)
    _assert_conf(overridden_configuration, False)
