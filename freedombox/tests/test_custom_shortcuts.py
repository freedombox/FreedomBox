# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom shortcuts.
"""

import json
import pathlib

from plinth.modules.api.views import get_shortcuts_as_json


def test_non_existent_custom_shortcuts_file(shortcuts_file):
    """Test loading a non-existent shortcuts file."""
    shortcuts_file('x-non-existant.json')
    get_shortcuts_as_json()


def test_blank_custom_shortcuts_file(shortcuts_file):
    """Test loading a shortcuts file that is blank."""
    shortcuts_file('blank.json')
    get_shortcuts_as_json()


def test_empty_custom_shortcuts_list(shortcuts_file):
    """Test loading a shortcuts file that has zero shortcuts."""
    shortcuts_file('empty.json')
    get_shortcuts_as_json()


def test_dotd_shortcuts_files(shortcuts_file):
    """Test loading a shortcuts file that has more files in .d directory."""
    shortcuts_file('dotd.json')
    shortcuts = get_shortcuts_as_json()
    assert len(shortcuts['shortcuts']) >= 2
    assert any(shortcut['name'] == 'NextCloud'
               for shortcut in shortcuts['shortcuts'])
    assert any(shortcut['name'] == 'NextCloud2'
               for shortcut in shortcuts['shortcuts'])


def test_custom_nextcloud_shortcut(shortcuts_file):
    """Test loading a shortcuts file that has nextcloud shortcut."""
    shortcuts_file('nextcloud.json')
    shortcuts = get_shortcuts_as_json()
    assert len(shortcuts['shortcuts']) >= 1
    assert any(shortcut['name'] == 'NextCloud'
               for shortcut in shortcuts['shortcuts'])


def test_retrieved_custom_shortcut(shortcuts_file):
    """Test the value of loaded nextcloud shortcut."""
    shortcuts_file('nextcloud.json')
    shortcuts = get_shortcuts_as_json()
    shortcut = [
        current_shortcut for current_shortcut in shortcuts['shortcuts']
        if current_shortcut['name'] == 'NextCloud'
    ]
    assert shortcut

    path = pathlib.Path(__file__).parent / 'data' / 'shortcuts'
    path /= 'nextcloud.json'
    assert shortcut[0] == json.loads(path.read_bytes())['shortcuts'][0]
