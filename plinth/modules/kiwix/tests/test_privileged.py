# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix actions.
"""

import pathlib
import pkg_resources
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
def fixture_kiwix_home(tmpdir):
    """Set Kiwix home to a new temporary directory
    initialized with an empty library file."""
    privileged.KIWIX_HOME = pathlib.Path(str(tmpdir / 'kiwix'))
    privileged.KIWIX_HOME.mkdir()
    privileged.CONTENT_DIR = privileged.KIWIX_HOME / 'content'
    privileged.CONTENT_DIR.mkdir()
    privileged.LIBRARY_FILE = privileged.KIWIX_HOME / 'library_zim.xml'
    with open(privileged.LIBRARY_FILE, 'w', encoding='utf_8') as library_file:
        library_file.write(EMPTY_LIBRARY_CONTENTS)


@pytest.fixture(autouse=True)
def fixture_patch():
    """Patch some underlying methods."""
    with patch('subprocess.check_call'), patch('subprocess.run'):
        yield


def test_add_content(tmpdir):
    """Test adding a content package to Kiwix."""
    some_dir = tmpdir / 'some' / 'dir'
    pathlib.Path(some_dir).mkdir(parents=True, exist_ok=True)
    zim_file_name = 'wikipedia_en_all_maxi_2022-05.zim'
    orig_file = some_dir / zim_file_name
    pathlib.Path(orig_file).touch()

    privileged.add_content(str(orig_file))
    assert (privileged.KIWIX_HOME / 'content' / zim_file_name).exists()
    assert not orig_file.exists()


def test_list_content_packages():
    """Test listing the content packages from a library file."""
    privileged.LIBRARY_FILE = pkg_resources.resource_filename(
        'plinth.modules.kiwix.tests', 'data/sample_library_zim.xml')
    content_packages = privileged.list_content_packages()
    assert content_packages[ZIM_ID] == {
        'title': 'FreedomBox',
        'description': 'A sample content archive',
        'path': 'freedombox'
    }


def test_delete_content_package():
    """Test deleting one content package."""
    sample_library_file = pkg_resources.resource_filename(
        'plinth.modules.kiwix.tests', 'data/sample_library_zim.xml')

    with open(sample_library_file, 'r',
              encoding='utf_8') as sample_library_file:
        with open(privileged.LIBRARY_FILE, 'w',
                  encoding='utf_8') as library_file:
            library_file.write(sample_library_file.read())

    zim_file = privileged.CONTENT_DIR / 'FreedomBox.zim'
    zim_file.touch()

    privileged.delete_content_package(ZIM_ID)

    assert not zim_file.exists()
    # Cannot check that the book is removed from library_zim.xml
