# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common test fixtures for OpenVPN.
"""

import importlib
import pathlib
import types
from unittest.mock import patch

import pytest

current_directory = pathlib.Path(__file__).parent


def _load_actions_module():
    actions_file_path = str(current_directory / '..' / '..' / '..' / '..' /
                            'actions' / 'openvpn')
    loader = importlib.machinery.SourceFileLoader('openvpn', actions_file_path)
    module = types.ModuleType(loader.name)
    loader.exec_module(module)
    return module


actions = _load_actions_module()


@pytest.fixture(name='keys_directory')
def fixture_keys_directory(tmp_path):
    return tmp_path


@pytest.fixture(name='call_action')
def fixture_call_action(capsys, keys_directory):
    """Run actions with overridden directory paths."""

    def _call_action(module_name, args, **kwargs):
        actions.DH_PARAMS = f'{keys_directory}/pki/dh.pem'
        actions.EC_PARAMS = f'{keys_directory}/pki/ecparams/secp521r1.pem'
        with patch('argparse._sys.argv', [module_name] + args):
            actions.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action
