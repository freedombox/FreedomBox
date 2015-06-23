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
Test module for custom Django template tags.
"""

import unittest

from plinth.templatetags.plinth_extras import mark_active_menuitem


class TestShowSubSubMenu(unittest.TestCase):
    """Verify that the highlighting of the subsubmenu is working correctly"""
    def assert_active_url(self, menu, url):
        """Verify that only the given url is set as 'active' in the menu"""
        for item in menu:
            if item['url'] == url:
                self.assertTrue(item['active'])
            else:
                self.assertFalse(item['active'])

    @staticmethod
    def _verify_active_menuitems(menu):
        """Verify that one and only one menuitem is marked as active"""
        return sum([item['active'] for item in menu]) == 1

    def test_highlighting(self):
        """Test detection of active subsubmenu items using request.path"""
        menu = [{'url': '/abc/123/abc/', 'text': 'abc'},
                {'url': '/abc/123/', 'text': 'overview'},
                {'url': '/abc/123/crunch/', 'text': 'crunch'},
                {'url': '/abc/123/create/', 'text': 'create'}]

        tests = [['/abc/123/crunch/new/', '/abc/123/crunch/'],
                 ['/abc/123/create/', '/abc/123/create/'],
                 ['/abc/123/nolink/', '/abc/123/'],
                 ['/abc/123/abx/', '/abc/123/'],
                 ['/abc/123/ab/', '/abc/123/'],
                 ['/abc/123/', '/abc/123/']]

        for check_path, expected_active_path in tests:
            menu = mark_active_menuitem(menu, check_path)
            self.assert_active_url(menu, expected_active_path)
            self.assertTrue(self._verify_active_menuitems(menu))
