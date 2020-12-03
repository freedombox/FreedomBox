# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for sso module operations.
"""

import imp
import os
import pathlib
from unittest.mock import patch

import pytest

from plinth.modules.sso.views import PRIVATE_KEY_FILE_NAME


def _action_file():
    """Return the path to the 'sso' actions file."""
    current_directory = pathlib.Path(__file__).parent
    return str(current_directory / '..' / '..' / '..' / '..' / 'actions' /
               'auth-pubtkt')


sso_actions = imp.load_source('sso', _action_file())


@pytest.fixture(name='call_action')
def fixture_call_action(tmpdir, capsys):
    """Run actions with custom keys path."""

    def _call_action(args, **kwargs):
        sso_actions.KEYS_DIRECTORY = str(tmpdir)
        with patch('argparse._sys.argv', ['sso'] + args):
            sso_actions.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action


@pytest.fixture(name='existing_key_pair')
def fixture_existing_key_pair(call_action):
    """A fixture to create key pair if needed."""
    call_action(['create-key-pair'])


def test_generate_ticket(call_action, existing_key_pair):
    """Test generating a ticket."""
    username = 'tester'
    groups = 'freedombox-share,syncthing,web-search'

    private_key_file = os.path.join(sso_actions.KEYS_DIRECTORY,
                                    PRIVATE_KEY_FILE_NAME)
    ticket = call_action([
        'generate-ticket', '--uid', username, '--private-key-file',
        private_key_file, '--tokens', groups
    ])

    fields = {}
    for item in ticket.split(';'):
        try:
            key, value = item.split('=')
            fields[key] = value
        except ValueError:
            # The 'sig' field can also contain '='.
            continue

    assert fields['uid'] == username
    assert int(fields['validuntil']) > 0
    assert fields['tokens'] == groups
    assert int(fields['graceperiod']) > 0
