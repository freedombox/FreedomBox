# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix actions.
"""

import pathlib
import shutil
from unittest.mock import patch

import pytest

from plinth.modules.kiwix import privileged

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.modules.kiwix.privileged']

EMPTY_LIBRARY_CONTENTS = '''<?xml version="1.0" encoding="UTF-8"?>
<library version="20110515">
</library>'''

ZIM_ID = 'bc4f8cdf-5626-2b13-3860-0033deddfbea'


@pytest.fixture(autouse=True)
def fixture_kiwix_home(tmp_path):
    """Create a new Kiwix home in a new temporary directory.

    Initialize with a sample, valid library file.
    """
    privileged.KIWIX_HOME = tmp_path / 'kiwix'
    privileged.KIWIX_HOME.mkdir()
    privileged.CONTENT_DIR = privileged.KIWIX_HOME / 'content'
    privileged.CONTENT_DIR.mkdir()
    privileged.LIBRARY_FILE = privileged.KIWIX_HOME / 'library_zim.xml'
    source_file = pathlib.Path(__file__).parent / 'data/sample_library_zim.xml'
    shutil.copy(source_file, privileged.LIBRARY_FILE)


@pytest.fixture(autouse=True)
def fixture_patch():
    """Patch some underlying methods."""
    with patch('subprocess.check_call'), patch('subprocess.run'), patch(
            'os.chown'):
        yield


def test_add_package(tmp_path):
    """Test adding a content package to Kiwix."""
    some_dir = tmp_path / 'some' / 'dir'
    some_dir.mkdir(parents=True, exist_ok=True)
    zim_file_name = 'wikipedia_en_all_maxi_2022-05.zim'
    orig_file = some_dir / zim_file_name
    orig_file.touch()

    privileged.add_package(str(orig_file))
    assert (privileged.KIWIX_HOME / 'content' / zim_file_name).exists()
    assert not orig_file.exists()


def test_list_packages():
    """Test listing the content packages from a library file."""
    content = privileged.list_packages()
    assert content[ZIM_ID] == {
        'title': 'FreedomBox',
        'description': 'A sample content archive',
        'path': 'freedombox'
    }


def test_delete_package():
    """Test deleting one content package."""
    zim_file = privileged.CONTENT_DIR / 'FreedomBox.zim'
    zim_file.touch()

    privileged.delete_package(ZIM_ID)

    assert not zim_file.exists()
    # Cannot check that the book is removed from library_zim.xml
