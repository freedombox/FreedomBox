#
# This file is part of Plinth.
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

from django.http import HttpRequest
from django.test import TestCase
from django.urls import reverse
import random

from plinth import menu as menu_module
from plinth.menu import Menu


URL_TEMPLATE = '/a{}/b{}/c{}/'


# Test helper methods

def build_menu(size=5):
    """Build a menu with the specified number of items."""
    random.seed()
    item_data = []
    for index in range(1, size + 1):
        item_data.append(['Item' + str(index),
                          'Icon' + str(index),
                          URL_TEMPLATE.format(index, index, index),
                          random.randint(0, 1000)])

    menu = Menu()
    for data in item_data:
        menu.add_item(data[0], data[1], data[2], data[3])

    return menu


def dump_menu(menu):
    """Dump the specified menu URL hierarchy to the console."""
    print()
    print('# # # # # # # # # #')
    print('Top level URL: %s' % menu.url)
    for item in menu.items:
        print('  Item URL: %s' % item.url)
    print('# # # # # # # # # #')


class MenuTestCase(TestCase):
    """Verify the behavior of the Plinth Menu class."""

    def test_init(self):
        """Verify that main_menu and essential items are created."""
        menu_module.init()
        main_menu = menu_module.main_menu
        self.assertIsInstance(main_menu, Menu)

        apps_menu = main_menu.get('apps')
        self.assertEqual(apps_menu.label, '')
        self.assertEqual(apps_menu.icon, 'glyphicon-download-alt')
        self.assertEqual(str(apps_menu.url), '/apps/')

        system_menu = main_menu.get('system')
        self.assertEqual(system_menu.label, '')
        self.assertEqual(system_menu.icon, 'glyphicon-cog')
        self.assertEqual(str(system_menu.url), '/sys/')

    def test_menu_creation_without_arguments(self):
        """Verify the Menu state without initialization parameters."""
        menu = Menu()
        self.assertEqual('', menu.label)
        self.assertEqual('', menu.icon)
        self.assertEqual('#', menu.url)
        self.assertEqual(50, menu.order)
        self.assertEqual(0, len(menu.items))

    def test_menu_creation_with_arguments(self):
        """Verify the Menu state with initialization parameters."""
        expected_label = 'Label'
        expected_icon = 'Icon'
        expected_url = '/aaa/bbb/ccc/'
        expected_order = 42
        menu = Menu(expected_label, expected_icon, expected_url,
                    expected_order)

        self.assertEqual(expected_label, menu.label)
        self.assertEqual(expected_icon, menu.icon)
        self.assertEqual(expected_url, menu.url)
        self.assertEqual(expected_order, menu.order)
        self.assertEqual(0, len(menu.items))

    def test_get(self):
        """Verify that a menu item can be correctly retrieved."""
        expected_label = 'Label2'
        expected_icon = 'Icon2'
        expected_url = 'index'
        reversed_url = reverse(expected_url)
        expected_order = 2
        menu = Menu()
        menu.add_item(expected_label, expected_icon, reversed_url,
                      expected_order)
        actual_item = menu.get(expected_url)

        self.assertIsNotNone(actual_item)
        self.assertEqual(expected_label, actual_item.label)
        self.assertEqual(expected_icon, actual_item.icon)
        self.assertEqual(reversed_url, actual_item.url)
        self.assertEqual(expected_order, actual_item.order)
        self.assertEqual(0, len(actual_item.items))

    def test_get_with_item_not_found(self):
        """Verify that a KeyError is raised if a menu item is not found."""
        expected_label = 'Label3'
        expected_icon = 'Icon3'
        expected_url = 'index'
        expected_order = 3
        menu = Menu()
        menu.add_item(expected_label, expected_icon, expected_url,
                      expected_order)

        self.assertRaises(KeyError, menu.get, expected_url)

    def test_sort_items(self):
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
            self.assertGreaterEqual(items[index].order, items[index - 1].order)
            if items[index].order == items[index - 1].order:
                self.assertGreaterEqual(items[index].label,
                                        items[index - 1].label)

    def test_add_urlname(self):
        """Verify that a named URL can be added to a menu correctly."""
        expected_label = 'Label4'
        expected_icon = 'Icon4'
        expected_url = 'index'
        reversed_url = reverse(expected_url)
        expected_order = 4
        menu = Menu()
        actual_item = menu.add_urlname(expected_label, expected_icon,
                                       expected_url, expected_order)

        self.assertEqual(1, len(menu.items))
        self.assertIsNotNone(actual_item)
        self.assertEqual(actual_item, menu.items[0])
        self.assertEqual(expected_label, actual_item.label)
        self.assertEqual(expected_icon, actual_item.icon)
        self.assertEqual(reversed_url, actual_item.url)
        self.assertEqual(expected_order, actual_item.order)
        self.assertEqual(0, len(actual_item.items))

    def test_add_item(self):
        """Verify that a menu item can be correctly added."""
        expected_label = 'Label5'
        expected_icon = 'Icon5'
        expected_url = '/jjj/kkk/lll/'
        expected_order = 5
        menu = Menu()
        actual_item = menu.add_item(expected_label, expected_icon,
                                    expected_url, expected_order)

        self.assertEqual(1, len(menu.items))
        self.assertIsNotNone(actual_item)
        self.assertEqual(actual_item, menu.items[0])
        self.assertEqual(expected_label, actual_item.label)
        self.assertEqual(expected_icon, actual_item.icon)
        self.assertEqual(expected_url, actual_item.url)
        self.assertEqual(expected_order, actual_item.order)
        self.assertEqual(0, len(actual_item.items))

    def test_active_item(self):
        """Verify that an active menu item can be correctly retrieved."""
        menu = build_menu()

        for index in range(1, 8):
            request = HttpRequest()
            request.path = URL_TEMPLATE.format(index, index, index)
            item = menu.active_item(request)
            if index <= 5:
                self.assertEqual('Item' + str(index), item.label)
                self.assertEqual(request.path, item.url)
            else:
                self.assertIsNone(item)

    def test_active_item_when_inside_subpath(self):
        """Verify that the current URL could be a sub-path of a menu item."""
        menu = build_menu()
        expected_url = URL_TEMPLATE.format(1, 1, 1)
        request = HttpRequest()
        request.path = expected_url + 'd/e/f/'
        item = menu.active_item(request)
        self.assertEqual('Item1', item.label)
        self.assertEqual(expected_url, item.url)
