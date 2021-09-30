# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for calibre actions.
"""

import json
import pathlib
from unittest.mock import call, patch

import pytest

actions_name = 'calibre'


@pytest.fixture(autouse=True)
def fixture_libraries_path(actions_module, tmpdir):
    """Set the libraries path in the actions module."""
    actions_module.LIBRARIES_PATH = pathlib.Path(str(tmpdir))


@pytest.fixture(autouse=True)
def fixture_patch():
    """Patch some underlying methods."""

    def side_effect(*args, **_kwargs):
        if args[0][0] != 'calibredb':
            return

        path = pathlib.Path(args[0][2]) / 'metadata.db'
        path.touch()

    with patch('subprocess.call') as subprocess_call, \
            patch('shutil.chown'):
        subprocess_call.side_effect = side_effect
        yield


def test_list_libraries(call_action):
    """Test listing libraries."""
    assert json.loads(call_action(['list-libraries'])) == {'libraries': []}
    call_action(['create-library', 'TestLibrary'])
    expected_output = {'libraries': ['TestLibrary']}
    assert json.loads(call_action(['list-libraries'])) == expected_output


@patch('shutil.chown')
def test_create_library(chown, call_action, actions_module):
    """Test creating a library."""
    call_action(['create-library', 'TestLibrary'])
    library = actions_module.LIBRARIES_PATH / 'TestLibrary'
    assert (library / 'metadata.db').exists()
    assert library.stat().st_mode == 0o40755
    expected_output = {'libraries': ['TestLibrary']}
    assert json.loads(call_action(['list-libraries'])) == expected_output

    chown.assert_has_calls([call(library.parent.parent, 'root', 'root')])


def test_delete_library(call_action):
    """Test deleting a library."""
    call_action(['create-library', 'TestLibrary'])

    call_action(['delete-library', 'TestLibrary'])
    assert json.loads(call_action(['list-libraries'])) == {'libraries': []}

    with pytest.raises(FileNotFoundError):
        call_action(['delete-library', 'TestLibrary'])
