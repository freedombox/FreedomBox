#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Test module for custom shortcuts.
"""

import json
import os

import pytest

from plinth import cfg
from plinth.modules.api.views import get_shortcuts_as_json

TEST_CONFIG_DIR = \
    os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')

CUSTOM_SHORTCUTS_FILE = os.path.join(TEST_CONFIG_DIR,
                                     'etc/plinth/custom-shortcuts.json')

NEXTCLOUD_SHORTCUT = {
    'name':
        'NextCloud',
    'short_description':
        'File Hosting Service',
    'description': [
        'Nextcloud is a suite of client-server software for creating '
        'and using file hosting services.'
    ],
    'icon_url':
        '/plinth/custom/static/themes/default/icons/nextcloud.png',
    'clients': [{
        'name': 'nextcloud',
        'platforms': [{
            'type': 'web',
            'url': '/nextcloud'
        }]
    }]
}


def setup_module(module):
    """Load test configuration."""
    root = os.path.dirname(os.path.realpath(__file__))
    cfg_file = os.path.join(TEST_CONFIG_DIR, 'etc', 'plinth', 'plinth.config')
    cfg.read(cfg_file, root)


def teardown_module(module):
    """Reset configuration."""
    cfg.read()


@pytest.fixture
def no_custom_shortcuts_file():
    """Delete the custom_shortcuts file."""
    if os.path.exists(CUSTOM_SHORTCUTS_FILE):
        os.remove(CUSTOM_SHORTCUTS_FILE)


@pytest.fixture
def blank_custom_shortcuts_file():
    """Create a blank shortcuts file."""
    open(CUSTOM_SHORTCUTS_FILE, 'w').close()


@pytest.fixture
def empty_custom_shortcuts():
    """Create a custom_shortcuts file with an empty list of shortcuts."""
    with open(CUSTOM_SHORTCUTS_FILE, 'w') as shortcuts_file:
        shortcuts = {'shortcuts': []}
        json.dump(shortcuts, shortcuts_file)


@pytest.fixture
def nextcloud_shortcut():
    with open(CUSTOM_SHORTCUTS_FILE, 'w') as shortcuts_file:
        shortcuts = {'shortcuts': [NEXTCLOUD_SHORTCUT]}
        json.dump(shortcuts, shortcuts_file)


def test_shortcuts_api_with_no_custom_shortcuts_file(no_custom_shortcuts_file):
    get_shortcuts_as_json()


def test_shortcuts_api_with_blank_custom_shortcuts_file(
        blank_custom_shortcuts_file):
    get_shortcuts_as_json()


def test_shortcuts_api_with_empty_custom_shortcuts_list(
        empty_custom_shortcuts):
    get_shortcuts_as_json()


def test_shortcuts_api_with_custom_nextcloud_shortcut(nextcloud_shortcut):
    shortcuts = get_shortcuts_as_json()
    assert len(shortcuts['shortcuts']) >= 1
    assert any(
        shortcut['name'] == 'NextCloud' for shortcut in shortcuts['shortcuts'])


def test_retrieved_custom_shortcut_from_api_is_correct(nextcloud_shortcut):
    shortcuts = get_shortcuts_as_json()
    nextcloud_shortcut = [
        shortcut for shortcut in shortcuts['shortcuts']
        if shortcut['name'] == 'NextCloud'
    ]
    assert nextcloud_shortcut
    assert nextcloud_shortcut[0] == NEXTCLOUD_SHORTCUT
