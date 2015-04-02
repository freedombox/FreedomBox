#!/usr/bin/python3
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

from django.http import HttpRequest
import unittest

from plinth import context_processors as cp


class ContextProcessorsTestCase(unittest.TestCase):
    """Verify behavior of the context_processors module."""

    @unittest.skip('requires configuring Django beforehand')
    def test_common(self):
        """Verify that the 'common' function returns the correct values."""
        request = HttpRequest()
        request.path = '/aaa/bbb/ccc/'
        response = cp.common(request)
        self.assertIsNotNone(response)

        config = response['cfg']
        self.assertIsNotNone(config)
        self.assertEqual('Plinth', config.product_name)
        self.assertEqual('FreedomBox', config.box_name)

        submenu = response['submenu']
        self.assertIsNone(submenu)

        urls = response['active_menu_urls']
        self.assertIsNotNone(urls)
        self.assertEqual(['/', '/aaa/', '/aaa/bbb/', '/aaa/bbb/ccc/'], urls)

    @unittest.skip('requires configuring Django beforehand')
    def test_common_border_conditions(self):
        """Verify that the 'common' functions works for border conditions."""
        request = HttpRequest()
        request.path = ''
        response = cp.common(request)
        self.assertEqual([], response['active_menu_urls'])

        request.path = '/'
        response = cp.common(request)
        self.assertEqual(['/'], response['active_menu_urls'])

        request.path = '/aaa/bbb'
        response = cp.common(request)
        self.assertEqual(['/', '/aaa/'], response['active_menu_urls'])


if __name__ == '__main__':
    unittest.main()
