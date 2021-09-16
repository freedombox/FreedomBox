# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common test fixtures for ejabberd.
"""

import importlib
import pathlib
import shutil
import types
from unittest.mock import MagicMock, patch

import pytest

from plinth.modules import ejabberd

current_directory = pathlib.Path(__file__).parent


def _load_actions_module():
    actions_file_path = str(current_directory / '..' / '..' / '..' / '..' /
                            'actions' / 'ejabberd')
    loader = importlib.machinery.SourceFileLoader('ejabberd',
                                                  actions_file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)
    return module


actions = _load_actions_module()


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


@pytest.fixture(name='call_action')
def fixture_call_action(capsys, conf_file, managed_file):
    """Run actions with custom root path."""

    def _call_action(module_name, args, **kwargs):
        actions.EJABBERD_CONFIG = conf_file
        actions.EJABBERD_MANAGED_COTURN = managed_file
        with patch('argparse._sys.argv', [module_name] + args):
            actions.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action


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
