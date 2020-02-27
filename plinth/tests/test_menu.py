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

URL_TEMPLATE = '/test/{}/{}/{}/'

# Test helper methods


def build_menu(size=5):
    """Build a menu with the specified number of items."""
    random.seed()

    menu = Menu('menu-index', url_name='index')

    for index in range(1, size + 1):
        kwargs = {
            'component_id': 'menu-test-' + str(index),
            'name': 'Name' + str(index),
            'short_description': 'ShortDescription' + str(index),
            'icon': 'Icon' + str(index),
            'url_name': 'test',
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
    Menu._all_menus = {}


def test_init():
    """Verify that main_menu and essential items are created."""
    menu_module.init()
    main_menu = menu_module.main_menu
    assert isinstance(main_menu, Menu)

    apps_menu = main_menu.get('apps')
    assert apps_menu.icon == 'fa-download'
    assert str(apps_menu.url) == '/apps/'

    system_menu = main_menu.get('system')
    assert system_menu.icon == 'fa-cog'
    assert str(system_menu.url) == '/sys/'


def test_menu_creation_without_arguments():
    """Verify the Menu state without initialization parameters."""
    with pytest.raises(ValueError):
        Menu('menu-test')

    menu = Menu('menu-index', url_name='index')
    assert menu.component_id == 'menu-index'
    assert menu.name is None
    assert menu.short_description is None
    assert menu.icon is None
    assert menu.url == '/'
    assert menu.order == 50
    assert not menu.advanced
    assert not menu.items


def test_menu_creation_with_arguments():
    """Verify the Menu state with initialization parameters."""
    expected_name = 'Name'
    expected_short_description = 'ShortDescription'
    expected_icon = 'Icon'
    url_name = 'test'
    url_kwargs = {'a': 1, 'b': 2, 'c': 3}
    expected_url = reverse(url_name, kwargs=url_kwargs)
    expected_order = 42
    parent_menu = Menu('menu-index', url_name='index')
    menu = Menu('menu-test', expected_name, expected_short_description,
                expected_icon, url_name, url_kwargs=url_kwargs,
                parent_url_name='index', order=expected_order, advanced=True)

    assert len(parent_menu.items) == 1
    assert parent_menu.items[0] == menu
    assert expected_name == menu.name
    assert expected_short_description == menu.short_description
    assert expected_icon == menu.icon
    assert expected_url == menu.url
    assert expected_order == menu.order
    assert menu.advanced
    assert not menu.items


def test_get():
    """Verify that a menu item can be correctly retrieved."""
    expected_name = 'Name2'
    expected_short_description = 'ShortDescription2'
    expected_icon = 'Icon2'
    expected_url = 'index'
    url_name = 'index'
    reversed_url = reverse(url_name)
    expected_order = 2
    menu = Menu('menu-test', expected_name, expected_short_description,
                expected_icon, url_name, order=expected_order, advanced=True)
    actual_item = menu.get(expected_url)

    assert actual_item is not None
    assert expected_name == actual_item.name
    assert expected_short_description == actual_item.short_description
    assert expected_icon == actual_item.icon
    assert reversed_url == actual_item.url
    assert expected_order == actual_item.order
    assert actual_item.advanced
    assert not actual_item.items


def test_get_with_item_not_found():
    """Verify that a KeyError is raised if a menu item is not found."""
    expected_name = 'Name3'
    expected_short_description = 'ShortDescription3'
    expected_icon = 'Icon3'
    url_name = 'index'
    expected_order = 3
    menu = Menu('menu-test', expected_name, expected_short_description,
                expected_icon, url_name, order=expected_order)

    with pytest.raises(KeyError):
        menu.get('apps')


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
        request.path = URL_TEMPLATE.format(index, index, index)
        item = menu.active_item(request)
        if index <= 5:
            assert request.path == item.url
        else:
            assert item is None


def test_active_item_when_inside_subpath():
    """Verify that the current URL could be a sub-path of a menu item."""
    menu = build_menu()
    expected_url = URL_TEMPLATE.format(1, 1, 1)
    request = HttpRequest()
    request.path = expected_url + 'd/e/f/'
    item = menu.active_item(request)
    assert expected_url == item.url
