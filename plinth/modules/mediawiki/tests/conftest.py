# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common test fixtures for MediaWiki.
"""

import shutil
import importlib
import pathlib
import types
from unittest.mock import patch

import pytest

current_directory = pathlib.Path(__file__).parent


def _load_actions_module():
    actions_file_path = str(current_directory / '..' / '..' / '..' / '..' /
                            'actions' / 'mediawiki')
    loader = importlib.machinery.SourceFileLoader('mediawiki',
                                                  actions_file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)
    return module


actions = _load_actions_module()


@pytest.fixture(name='call_action')
def fixture_call_action(capsys, conf_file):
    """Run actions with custom root path."""

    def _call_action(module_name, args, **kwargs):
        actions.CONF_FILE = conf_file
        with patch('argparse._sys.argv', [module_name] + args):
            actions.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action


@pytest.fixture(name='conf_file')
def fixture_conf_file(tmp_path):
    """Uses a dummy configuration file."""
    settings_file_name = 'FreedomBoxSettings.php'
    conf_file = tmp_path / settings_file_name
    conf_file.touch()
    shutil.copyfile(
        str(current_directory / '..' / 'data' / 'etc' / 'mediawiki' /
            settings_file_name), str(conf_file))
    return str(conf_file)
