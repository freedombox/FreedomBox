# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for sso module operations.
"""

import os

import pytest

from plinth.modules.sso.views import PRIVATE_KEY_FILE_NAME

actions_name = 'auth-pubtkt'


@pytest.fixture(autouse=True)
def fixture_keys_directory(actions_module, tmpdir):
    """Set keys directory in the actions module."""
    actions_module.KEYS_DIRECTORY = str(tmpdir)


@pytest.fixture(name='existing_key_pair')
def fixture_existing_key_pair(call_action):
    """A fixture to create key pair if needed."""
    call_action(['create-key-pair'])


def test_generate_ticket(call_action, existing_key_pair, actions_module):
    """Test generating a ticket."""
    username = 'tester'
    groups = 'freedombox-share,syncthing,web-search'

    private_key_file = os.path.join(actions_module.KEYS_DIRECTORY,
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
