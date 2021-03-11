# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common test fixtures for Matrix Synapse.
"""

import importlib
import pathlib
import types
from unittest.mock import patch

import pytest

current_directory = pathlib.Path(__file__).parent


def _load_actions_module():
    actions_file_path = str(current_directory / '..' / '..' / '..' / '..' /
                            'actions' / 'matrixsynapse')
    loader = importlib.machinery.SourceFileLoader('matrixsynapse',
                                                  actions_file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)
    return module


actions = _load_actions_module()


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


@pytest.fixture(name='call_action')
def fixture_call_action(capsys, managed_turn_conf_file,
                        overridden_turn_conf_file):
    """Run actions with custom root path."""

    def _call_action(module_name, args, **kwargs):
        actions.TURN_CONF_PATH = managed_turn_conf_file
        actions.OVERRIDDEN_TURN_CONF_PATH = overridden_turn_conf_file
        with patch('argparse._sys.argv', [module_name] +
                   args), patch('plinth.action_utils.service_try_restart'):
            actions.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action
