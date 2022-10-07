# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test module for calibre actions."""

import pathlib
from unittest.mock import call, patch

import pytest

from plinth.modules.calibre import privileged

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.modules.calibre.privileged']


@pytest.fixture(autouse=True)
def fixture_libraries_path(tmpdir):
    """Set the libraries path in the actions module."""
    privileged.LIBRARIES_PATH = pathlib.Path(str(tmpdir))


@pytest.fixture(autouse=True)
def fixture_patch():
    """Patch some underlying methods."""

    def side_effect(*args, **_kwargs):
        if args[0][0] != 'calibredb':
            return

        path = pathlib.Path(args[0][2]) / 'metadata.db'
        path.touch()

    with patch('subprocess.call') as subprocess_call, \
         patch('subprocess.run'), patch('shutil.chown'):
        subprocess_call.side_effect = side_effect
        yield


def test_list_libraries():
    """Test listing libraries."""
    assert privileged.list_libraries() == []
    privileged.create_library('TestLibrary')
    assert privileged.list_libraries() == ['TestLibrary']


@patch('shutil.chown')
def test_create_library(chown):
    """Test creating a library."""
    privileged.create_library('TestLibrary')
    library = privileged.LIBRARIES_PATH / 'TestLibrary'
    assert (library / 'metadata.db').exists()
    assert library.stat().st_mode == 0o40755
    assert privileged.list_libraries() == ['TestLibrary']

    chown.assert_has_calls([call(library.parent.parent, 'root', 'root')])


def test_delete_library():
    """Test deleting a library."""
    privileged.create_library('TestLibrary')
    privileged.delete_library('TestLibrary')
    assert privileged.list_libraries() == []

    with pytest.raises(FileNotFoundError):
        privileged.delete_library('TestLibrary')
