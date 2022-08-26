# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for sso module operations.
"""

import os

import pytest

from plinth.modules.sso import privileged
from plinth.modules.sso.views import PRIVATE_KEY_FILE_NAME

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.modules.sso.privileged']


@pytest.fixture(autouse=True)
def fixture_keys_directory(tmpdir):
    """Set keys directory in the actions module."""
    privileged.KEYS_DIRECTORY = str(tmpdir)


@pytest.fixture(name='existing_key_pair')
def fixture_existing_key_pair():
    """A fixture to create key pair if needed."""
    privileged.create_key_pair()


def test_generate_ticket(existing_key_pair):
    """Test generating a ticket."""
    username = 'tester'
    groups = ['freedombox-share', 'syncthing', 'web-search']

    private_key_file = os.path.join(privileged.KEYS_DIRECTORY,
                                    PRIVATE_KEY_FILE_NAME)
    ticket = privileged.generate_ticket(username, private_key_file, groups)

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
    assert fields['tokens'] == ','.join(groups)
    assert int(fields['graceperiod']) > 0
