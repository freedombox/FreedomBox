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

import pytest

from plinth.modules.api.views import get_shortcuts_as_json

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


@pytest.fixture(name='custom_shortcuts_file')
def fixture_custom_shortcuts_file(load_cfg, tmp_path):
    """Fixture to set path for a custom shortcuts file."""
    load_cfg.config_file = str(tmp_path / 'plinth.conf')
    return tmp_path / 'custom-shortcuts.json'


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


@pytest.fixture(name='nextcloud_shortcut')
def fixture_nextcloud_shortcut(custom_shortcuts_file):
    """Create a custom_shortcuts file with NextCloud shortcut."""
    shortcuts = {'shortcuts': [NEXTCLOUD_SHORTCUT]}
    custom_shortcuts_file.write_text(json.dumps(shortcuts))


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
    assert any(
        shortcut['name'] == 'NextCloud' for shortcut in shortcuts['shortcuts'])


@pytest.mark.usefixtures('nextcloud_shortcut')
def test_retrieved_custom_shortcut_from_api_is_correct():
    shortcuts = get_shortcuts_as_json()
    shortcut = [
        current_shortcut for current_shortcut in shortcuts['shortcuts']
        if current_shortcut['name'] == 'NextCloud'
    ]
    assert shortcut
    assert shortcut[0] == NEXTCLOUD_SHORTCUT
