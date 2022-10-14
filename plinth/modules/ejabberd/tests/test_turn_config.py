# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for ejabberd STUN/TURN configuration.
"""

import pathlib
import shutil
from unittest.mock import Mock, patch

import pytest

from plinth.modules import ejabberd
from plinth.modules.coturn.components import TurnConfiguration
from plinth.modules.ejabberd import privileged

managed_configuration = TurnConfiguration(
    'freedombox.local', [],
    'aiP02OAGyOlj6WGuCyqj7iaOsbkC7BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51')

overridden_configuration = TurnConfiguration(
    'public.coturn.site', [],
    'BUeKvKzhAsTZ8MEwMd3yTwpr2uvbOxgWe51aiP02OAGyOlj6WGuCyqj7iaOsbkC7')

pytestmark = pytest.mark.usefixtures('mock_privileged')
current_directory = pathlib.Path(__file__).parent
privileged_modules_to_mock = ['plinth.modules.ejabberd.privileged']


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
def fixture_set_configuration_paths(conf_file, managed_file):
    """Setup configuration file paths in action module."""
    privileged.EJABBERD_CONFIG = conf_file
    privileged.EJABBERD_MANAGED_COTURN = managed_file


@pytest.fixture(name='test_configuration', autouse=True)
def fixture_test_configuration(conf_file):
    """Use a separate ejabberd configuration for tests.

    The module state is patched to be 'up-to-date'.
    """
    with patch('plinth.app.App.get') as app_get:
        app = Mock()
        app_get.return_value = app
        app.needs_setup.return_value = False
        yield


def _set_turn_configuration(config=managed_configuration, managed=True):
    with patch('plinth.action_utils.service_is_running', return_value=False):
        ejabberd.update_turn_configuration(config, managed=managed)


def _assert_conf(expected_configuration, expected_managed):
    """Assert that ejabberd TURN configuration is as expected."""
    config, managed = ejabberd.get_turn_configuration()
    assert config.uris == expected_configuration.uris
    assert config.shared_secret == expected_configuration.shared_secret
    assert managed == expected_managed


def test_managed_turn_server_configuration():
    _set_turn_configuration()
    _assert_conf(managed_configuration, True)


def test_overridden_turn_server_configuration():
    _set_turn_configuration(overridden_configuration, False)
    _assert_conf(overridden_configuration, False)


def test_remove_turn_configuration():
    _set_turn_configuration()
    _set_turn_configuration(TurnConfiguration(), False)
    _assert_conf(TurnConfiguration(), False)
