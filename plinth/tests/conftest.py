# SPDX-License-Identifier: AGPL-3.0-or-later
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
    load_cfg.config_dir = str(tmp_path)
    return tmp_path / 'custom-shortcuts.json'


@pytest.fixture(name='nextcloud_shortcut')
def fixture_nextcloud_shortcut(custom_shortcuts_file):
    """Create a custom_shortcuts file with NextCloud shortcut."""
    shortcuts = {'shortcuts': [NEXTCLOUD_SHORTCUT]}
    custom_shortcuts_file.write_text(json.dumps(shortcuts))
