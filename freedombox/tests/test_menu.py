# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for menus.
"""

import random

import pytest
from django.http import HttpRequest
from django.urls import reverse

from plinth import menu as menu_module
from plinth.menu import Menu

URL_TEMPLATE = '/test{}/{}/{}/{}/'

# Test helper methods


def build_menu(size=5):
    """Build a menu with the specified number of items."""
    random.seed()

    menu = Menu('menu-index', url_name='index')

    for index in range(1, size + 1):
        kwargs = {
            'component_id': f'menu-test-{index}',
            'name': f'Name{index}',
            'icon': f'Icon{index}',
            'tags': ['tag1', 'tag2'],
            'url_name': f'test{index}',
            'url_kwargs': {
                'a': index,
                'b': index,
                'c': index
            },
            'parent_url_name': 'index',
            'order': random.randint(0, 1000),
        }

        Menu(**kwargs)

    return menu


@pytest.fixture(name='empty_menus', autouse=True)
def fixture_empty_menus():
    """Remove all menu entries before starting a test."""
    Menu._all_menus = set()


def test_init(rf):
    """Verify that main_menu and essential items are created."""
    menu_module.init()
    main_menu = menu_module.main_menu
    assert isinstance(main_menu, Menu)

    apps_menu = main_menu.active_item(rf.get('/apps/foo/'))
    assert apps_menu.icon == 'fa-download'
    assert str(apps_menu.url) == '/apps/'

    system_menu = main_menu.active_item(rf.get('/sys/bar/'))
    assert system_menu.icon == 'fa-cog'
    assert str(system_menu.url) == '/sys/'


def test_menu_creation_without_arguments():
    """Verify the Menu state without initialization parameters."""
    with pytest.raises(ValueError):
        Menu('menu-test')

    menu = Menu('menu-index', url_name='index')
    assert menu.component_id == 'menu-index'
    assert menu.name is None
    assert menu.icon is None
    assert menu.tags is None
    assert menu.url == '/'
    assert menu.order == 50
    assert not menu.advanced
    assert not menu.items


def test_menu_creation_with_arguments():
    """Verify the Menu state with initialization parameters."""
    expected_name = 'Name'
    expected_icon = 'Icon'
    expected_tags = ['tag1', 'tag2']
    url_name = 'test'
    url_kwargs = {'a': 1, 'b': 2, 'c': 3}
    expected_url = reverse(url_name, kwargs=url_kwargs)
    expected_order = 42
    parent_menu = Menu('menu-index', url_name='index')
    menu = Menu('menu-test', expected_name, expected_icon, expected_tags,
                url_name, url_kwargs=url_kwargs, parent_url_name='index',
                order=expected_order, advanced=True)

    assert menu.parent_url_name == 'index'
    assert len(parent_menu.items) == 1
    assert parent_menu.items[0] == menu
    assert expected_name == menu.name
    assert expected_icon == menu.icon
    assert expected_tags == menu.tags
    assert expected_url == menu.url
    assert expected_order == menu.order
    assert menu.advanced
    assert url_name == menu.url_name
    assert menu.url_args is None
    assert url_kwargs == menu.url_kwargs
    assert not menu.items


def test_sort_items():
    """Verify that menu items are sorted correctly."""
    size = 1000
    menu = build_menu(size)

    for index in range(0, 200):
        menu.items[index].order = 100

    # Verify that the order of every item is equal to or greater
    # than the order of the item preceding it and if the order is
    # the same, the names are considered.
    items = menu.sorted_items()
    for index in range(1, size):
        assert items[index].order >= items[index - 1].order
        if items[index].order == items[index - 1].order:
            assert items[index].name >= items[index - 1].name


def test_active_item():
    """Verify that an active menu item can be correctly retrieved."""
    menu = build_menu()

    for index in range(1, 8):
        request = HttpRequest()
        request.path = URL_TEMPLATE.format(index, index, index, index)
        item = menu.active_item(request)
        if index <= 5:
            assert request.path == item.url
        else:
            assert item is None


def test_active_item_when_inside_subpath():
    """Verify that the current URL could be a sub-path of a menu item."""
    menu = build_menu()
    expected_url = URL_TEMPLATE.format(1, 1, 1, 1)
    request = HttpRequest()
    request.path = expected_url + 'd/e/f/'
    item = menu.active_item(request)
    assert expected_url == item.url


def test_get_with_url_name():
    """Verify that menu item can be retrieved from all items."""
    build_menu()

    menu = Menu.get_with_url_name('test5')
    assert menu.name == 'Name5'
    with pytest.raises(LookupError):
        Menu.get_with_url_name('x-non-existent')
