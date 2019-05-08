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

    menu = Menu()

    for index in range(1, size + 1):
        args = [
            'Name' + str(index), 'Icon' + str(index), 'test',
            'ShortDescription' + str(index),
            random.randint(0, 1000)
        ]
        kwargs = {'url_kwargs': {'a': index, 'b': index, 'c': index}}

        menu.add_urlname(*args, **kwargs)

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
    menu = Menu()
    assert menu.icon == ''
    assert menu.url == '#'
    assert menu.order == 50
    assert not menu.items


def test_menu_creation_with_arguments():
    """Verify the Menu state with initialization parameters."""
    expected_name = 'Name'
    expected_short_description = 'ShortDescription'
    expected_icon = 'Icon'
    expected_url = '/aaa/bbb/ccc/'
    expected_order = 42
    menu = Menu(expected_name, expected_short_description, expected_icon,
                expected_url, expected_order)

    assert expected_name == menu.name
    assert expected_short_description == menu.short_description
    assert expected_icon == menu.icon
    assert expected_url == menu.url
    assert expected_order == menu.order
    assert not menu.items


def test_get():
    """Verify that a menu item can be correctly retrieved."""
    expected_name = 'Name2'
    expected_short_description = 'ShortDescription2'
    expected_icon = 'Icon2'
    expected_url = 'index'
    reversed_url = reverse(expected_url)
    expected_order = 2
    menu = Menu()
    menu.add_urlname(expected_name, expected_icon, expected_url,
                     expected_short_description, expected_order)
    actual_item = menu.get(expected_url)

    assert actual_item is not None
    assert expected_name == actual_item.name
    assert expected_short_description == actual_item.short_description
    assert expected_icon == actual_item.icon
    assert reversed_url == actual_item.url
    assert expected_order == actual_item.order
    assert not actual_item.items


def test_get_with_item_not_found():
    """Verify that a KeyError is raised if a menu item is not found."""
    expected_name = 'Name3'
    expected_short_description = 'ShortDescription3'
    expected_icon = 'Icon3'
    expected_url = 'index'
    expected_order = 3
    menu = Menu()
    menu.add_urlname(expected_name, expected_icon, expected_url,
                     expected_short_description, expected_order)

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
    # the same, the labels are considered.
    items = menu.sorted_items()
    for index in range(1, size):
        assert items[index].order >= items[index - 1].order
        if items[index].order == items[index - 1].order:
            assert items[index].name >= items[index - 1].name


def test_add_urlname():
    """Verify that a named URL can be added to a menu correctly."""
    expected_name = 'Name4'
    expected_short_description = 'Description4'
    expected_icon = 'Icon4'
    expected_url = 'index'
    reversed_url = reverse(expected_url)
    expected_order = 4
    menu = Menu()
    actual_item = menu.add_urlname(expected_name, expected_icon, expected_url,
                                   expected_short_description, expected_order)

    assert len(menu.items) == 1
    assert actual_item is not None
    assert actual_item == menu.items[0]
    assert expected_name == actual_item.name
    assert expected_icon == actual_item.icon
    assert reversed_url == actual_item.url
    assert expected_order == actual_item.order
    assert not actual_item.items


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
