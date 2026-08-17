# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for frontpage.
"""

from unittest.mock import patch

import pytest

from plinth.frontpage import Shortcut, add_custom_shortcuts

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
    assert shortcut.url == '?selected=test-component'
    assert shortcut.icon is None
    assert shortcut.description is None
    assert shortcut.manual_page is None
    assert shortcut.configure_url is None
    assert shortcut.clients is None
    assert shortcut.tags is None
    assert not shortcut.login_required
    assert shortcut.allowed_groups is None
    assert Shortcut._all_shortcuts['test-component'] == shortcut


def test_shortcut_init():
    """Test initializing shortcut component."""
    clients = ['client1', 'client2']
    allowed_groups = ['group1', 'group2']
    shortcut = Shortcut('test-component', name='test-name', url='test-url',
                        icon='test-icon', description='test-description',
                        manual_page='TestPage',
                        configure_url='test-configure-url', clients=clients,
                        tags=['tag1', 'tag2'], login_required=True,
                        allowed_groups=allowed_groups)
    assert shortcut.url == 'test-url'
    assert shortcut.icon == 'test-icon'
    assert shortcut.description == 'test-description'
    assert shortcut.manual_page == 'TestPage'
    assert shortcut.configure_url == 'test-configure-url'
    assert shortcut.clients == clients
    assert shortcut.tags == ['tag1', 'tag2']
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
                 login_required=True, allowed_groups=['group1']),
        Shortcut('group2-web-app-component-1', 'name3', 'short2', url='url3',
                 login_required=True, allowed_groups=['group2']),
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


def test_shortcut_list_web_apps_only(common_shortcuts):
    """Test listing only web app shortcuts."""
    cuts = common_shortcuts

    return_list = Shortcut.list()
    assert Shortcut.list() == [cuts[0], cuts[1], cuts[2], cuts[3]]

    return_list = Shortcut.list(web_apps_only=False)
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    return_list = Shortcut.list(web_apps_only=True)
    assert return_list == [cuts[0], cuts[1], cuts[2]]


@patch('plinth.modules.users.privileged.get_user_groups')
def test_shortcut_list_with_username(get_user_groups, common_shortcuts):
    """Test listing for particular users."""
    cuts = common_shortcuts

    return_list = Shortcut.list()
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    get_user_groups.return_value = ['admin']
    return_list = Shortcut.list(username='admin')
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    get_user_groups.return_value = ['group1']
    return_list = Shortcut.list(username='user1')
    assert return_list == [cuts[0], cuts[1], cuts[3]]

    get_user_groups.return_value = ['group1', 'group2']
    return_list = Shortcut.list(username='user2')
    assert return_list == [cuts[0], cuts[1], cuts[2], cuts[3]]

    cut = Shortcut('group2-web-app-component-1', 'name5', 'short2', url='url4',
                   login_required=False, allowed_groups=['group3'])
    get_user_groups.return_value = ['group3']
    return_list = Shortcut.list(username='user3')
    assert return_list == [cuts[0], cuts[3], cut]

    get_user_groups.return_value = ['group4']
    return_list = Shortcut.list(username='user4')
    assert return_list == [cuts[0], cuts[3], cut]


def test_add_custom_shortcuts(shortcuts_file):
    """Test that adding custom shortcuts succeeds."""
    shortcuts_file('nextcloud.json')
    add_custom_shortcuts()
