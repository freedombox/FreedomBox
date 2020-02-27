# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test I2P router configuration editing helper.
"""

import pytest

from plinth.modules.i2p.helpers import RouterEditor
from plinth.modules.i2p.tests import DATA_DIR

ROUTER_CONF_PATH = str(DATA_DIR / 'router.config')


@pytest.fixture(name='editor')
def fixture_editor():
    """Return editor instance object for each test."""
    return RouterEditor(ROUTER_CONF_PATH)


def test_count_favorites(editor):
    """Test counting favorites."""
    editor.read_conf()
    favorites = editor.get_favorites()
    assert len(favorites.keys()) == 17


def test_add_normal_favorite(editor):
    """Test adding a normal favorite."""
    editor.read_conf()
    name = 'Somewhere'
    url = 'http://somewhere-again.i2p'
    description = "Just somewhere else"
    editor.add_favorite(name, url, description)

    favorites = editor.get_favorites()
    assert url in favorites
    favorite = favorites[url]
    assert favorite['name'] == name
    assert favorite['description'] == description

    assert len(favorites) == 18


def test_add_favorite_with_comma(editor):
    """Test adding a favorite with common in its name."""
    editor.read_conf()
    name = 'Name,with,comma'
    expected_name = name.replace(',', '.')
    url = 'http://url-without-comma.i2p'
    description = "Another,comma,to,play,with"
    expected_description = description.replace(',', '.')

    editor.add_favorite(name, url, description)

    favorites = editor.get_favorites()
    assert url in favorites
    favorite = favorites[url]
    assert favorite['name'] == expected_name
    assert favorite['description'] == expected_description

    assert len(favorites) == 18


def test_add_fav_to_empty_config(editor):
    """Test adding favorite to empty configuration."""
    editor.conf_filename = '/tmp/inexistent.conf'
    editor.read_conf()
    assert not editor.get_favorites()

    name = 'Test Favorite'
    url = 'http://test-fav.i2p'
    editor.add_favorite(name, url)
    assert len(editor.get_favorites()) == 1
