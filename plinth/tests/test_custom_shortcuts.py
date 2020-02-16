# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom shortcuts.
"""

import json

import pytest

from plinth.modules.api.views import get_shortcuts_as_json

from .conftest import NEXTCLOUD_SHORTCUT


@pytest.fixture(name='no_custom_shortcuts_file')
def fixture_no_custom_shortcuts_file(custom_shortcuts_file):
    """Delete the custom_shortcuts file."""
    if custom_shortcuts_file.exists():
        custom_shortcuts_file.unlink()


@pytest.fixture(name='blank_custom_shortcuts_file')
def fixture_blank_custom_shortcuts_file(custom_shortcuts_file):
    """Create a blank shortcuts file."""
    custom_shortcuts_file.write_text('')


@pytest.fixture(name='empty_custom_shortcuts')
def fixture_empty_custom_shortcuts(custom_shortcuts_file):
    """Create a custom_shortcuts file with an empty list of shortcuts."""
    custom_shortcuts_file.write_text(json.dumps({'shortcuts': []}))


@pytest.mark.usefixtures('no_custom_shortcuts_file')
def test_shortcuts_api_with_no_custom_shortcuts_file():
    get_shortcuts_as_json()


@pytest.mark.usefixtures('blank_custom_shortcuts_file')
def test_shortcuts_api_with_blank_custom_shortcuts_file():
    get_shortcuts_as_json()


@pytest.mark.usefixtures('empty_custom_shortcuts')
def test_shortcuts_api_with_empty_custom_shortcuts_list():
    get_shortcuts_as_json()


@pytest.mark.usefixtures('nextcloud_shortcut')
def test_shortcuts_api_with_custom_nextcloud_shortcut():
    shortcuts = get_shortcuts_as_json()
    assert len(shortcuts['shortcuts']) >= 1
    assert any(shortcut['name'] == 'NextCloud'
               for shortcut in shortcuts['shortcuts'])


@pytest.mark.usefixtures('nextcloud_shortcut')
def test_retrieved_custom_shortcut_from_api_is_correct():
    shortcuts = get_shortcuts_as_json()
    shortcut = [
        current_shortcut for current_shortcut in shortcuts['shortcuts']
        if current_shortcut['name'] == 'NextCloud'
    ]
    assert shortcut
    assert shortcut[0] == NEXTCLOUD_SHORTCUT
