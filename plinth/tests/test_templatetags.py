#!/usr/bin/python3
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-
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

import unittest

from plinth.templatetags.plinth_extras import mark_active_menuitem


class TestPrivileged(unittest.TestCase):
    """Verify that the highlighting of the subsubmenu is working correctly"""

    def is_active_url(self, menu, url):
        """Verify that only the given url is set as 'active' in the menu"""
        for urlitem in menu['items']:
            if urlitem['url'] == url and not urlitem['active']:
                return False
            if urlitem['url'] != url and urlitem['active']:
                return False
        return True

    def verify_active_menuitems(self, menu):
        """Verify that one and only one menuitem is marked as active"""
        return sum([x['active'] for x in menu['items']])==1

    def test_highlighting(self):
        """Test detection of active subsubmenu items using request.path"""
        menu = {
            "text": "blubb",
            "items": [{'url': '/abc/123/abc/', 'text': 'abc'},
                      {'url': '/abc/123/', 'text': 'overview'},
                      {'url': '/abc/123/crunch/', 'text': 'crunch'},
                      {'url': '/abc/123/create/', 'text': 'create'}]
        }

        menu = mark_active_menuitem(menu, '/abc/123/crunch/new/')
        assert(self.is_active_url(menu, '/abc/123/crunch/'))
        assert(self.verify_active_menuitems(menu))

        menu = mark_active_menuitem(menu, '/abc/123/create/')
        assert(self.is_active_url(menu, '/abc/123/create/'))
        assert(self.verify_active_menuitems(menu))

        menu = mark_active_menuitem(menu, '/abc/123/nolink/')
        assert(self.is_active_url(menu, '/abc/123/'))
        assert(self.verify_active_menuitems(menu))

        menu = mark_active_menuitem(menu, '/abc/123/abx/')
        assert(self.is_active_url(menu, '/abc/123/'))
        assert(self.verify_active_menuitems(menu))

        menu = mark_active_menuitem(menu, '/abc/123/')
        assert(self.is_active_url(menu, '/abc/123/'))
        assert(self.verify_active_menuitems(menu))
