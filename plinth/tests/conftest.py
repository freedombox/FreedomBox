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
pytest configuration for all tests in the plinth/tests/ directory.
"""

import json

import pytest

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


@pytest.fixture(name='nextcloud_shortcut')
def fixture_nextcloud_shortcut(custom_shortcuts_file):
    """Create a custom_shortcuts file with NextCloud shortcut."""
    shortcuts = {'shortcuts': [NEXTCLOUD_SHORTCUT]}
    custom_shortcuts_file.write_text(json.dumps(shortcuts))
