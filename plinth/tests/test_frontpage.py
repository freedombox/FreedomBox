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
Test module for frontpage.
"""

from unittest.mock import patch

import pytest

from plinth.frontpage import Shortcut, add_custom_shortcuts

from .test_custom_shortcuts import (fixture_custom_shortcuts_file,
                                    fixture_nextcloud_shortcut)

# pylint: disable=protected-access


@pytest.fixture(name='clean_global_shortcuts', autouse=True)
def fixture_clean_global_shortcuts():
    """Ensure that global list of shortcuts is clean."""
    Shortcut._all_shortcuts = {}


def test_shortcut_init_with_arguments():
    """Test initializing shortcut component without arguments."""
    with pytest.raises(ValueError):
        Shortcut(None, None)

    shortcut = Shortcut('test-component', 'test-name')
    assert shortcut.component_id == 'test-component'
    assert shortcut.name == 'test-name'
    assert shortcut.short_description is None
    assert shortcut.url == '?selected=test-component'
    assert shortcut.icon is None
    assert shortcut.description is None
    assert shortcut.configure_url is None
    assert shortcut.clients is None
    assert not shortcut.login_required
    assert shortcut.allowed_groups is None
    assert Shortcut._all_shortcuts['test-component'] == shortcut


def test_shortcut_init():
    """Test initializing shortcut component."""
    clients = ['client1', 'client2']
    allowed_groups = ['group1', 'group2']
    shortcut = Shortcut('test-component', name='test-name',
                        short_description='test-short-description',
                        url='test-url', icon='test-icon',
                        description='test-description',
                        configure_url='test-configure-url', clients=clients,
                        login_required=True, allowed_groups=allowed_groups)
    assert shortcut.short_description == 'test-short-description'
    assert shortcut.url == 'test-url'
    assert shortcut.icon == 'test-icon'
    assert shortcut.description == 'test-description'
    assert shortcut.configure_url == 'test-configure-url'
    assert shortcut.clients == clients
    assert shortcut.login_required
    assert shortcut.allowed_groups == set(allowed_groups)


def test_shortcut_remove():
    """Test removing a shortcut global list of shortcuts."""
    shortcut = Shortcut('test-component', None)
    shortcut.remove()
    with pytest.raises(KeyError):
        del Shortcut._all_shortcuts['test-component']


@pytest.fixture(name='common_shortcuts')
def fixture_common_shortcuts(clean_global_shortcuts):
    """Create some common shortcuts."""
    shortcuts = [
        Shortcut('anon-web-app-component-1', 'name1', 'short4', url='url1'),
        Shortcut('group1-web-app-component-1', 'Name2', 'Short3', url='url2',
                 allowed_groups=['group1']),
        Shortcut('group2-web-app-component-1', 'name3', 'short2', url='url3',
                 allowed_groups=['group2']),
        Shortcut('anon-non-web-app-component-1', 'name4', 'short1', url=None),
    ]
    return shortcuts


def test_shortcut_list_sorting(common_shortcuts):
    """Test listing shortcuts in sorted order."""
    cuts = common_shortcuts

    return_list = Shortcut.list()
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    return_list = Shortcut.list(sort_by='name')
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    return_list = Shortcut.list(sort_by='short_description')
    assert return_list == [cuts[3], cuts[2], cuts[1], cuts[0]]


def test_shortcut_list_web_apps_only(common_shortcuts):
    """Test listing only web app shortcuts."""
    cuts = common_shortcuts

    return_list = Shortcut.list()
    assert Shortcut.list() == [cuts[0], cuts[1], cuts[2], cuts[3]]

    return_list = Shortcut.list(web_apps_only=False)
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    return_list = Shortcut.list(web_apps_only=True)
    assert return_list == [cuts[0], cuts[1], cuts[2]]


@patch('plinth.actions.superuser_run')
def test_shortcut_list_with_username(superuser_run, common_shortcuts):
    """Test listing for particular users."""
    cuts = common_shortcuts

    return_list = Shortcut.list()
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    superuser_run.return_value = 'admin'
    return_list = Shortcut.list(username='admin')
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    superuser_run.return_value = 'group1'
    return_list = Shortcut.list(username='user1')
    assert return_list == [cuts[0], cuts[1], cuts[3]]

    superuser_run.return_value = 'group1\ngroup2'
    return_list = Shortcut.list(username='user2')
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]


@pytest.mark.usefixtures('nextcloud_shortcut')
def test_add_custom_shortcuts():
    """Test that adding custom shortcuts succeeds."""
    add_custom_shortcuts()
