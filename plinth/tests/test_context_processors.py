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
Test module for Plinth's custom context processors.
"""
from unittest.mock import Mock, MagicMock

from django.http import HttpRequest
from django.test import TestCase

from plinth import cfg
from plinth import context_processors as cp
from plinth import menu


def setUpModule():  # noqa
    """Setup all test cases by initializing menu module."""
    menu.init()


class ContextProcessorsTestCase(TestCase):
    """Verify behavior of the context_processors module."""

    def test_common(self):
        """Verify that the common() function returns the correct values."""
        cfg.read()      # initialize config settings

        request = HttpRequest()
        request.path = '/aaa/bbb/ccc/'
        request.user = Mock()
        request.user.groups.filter().exists = Mock(return_value=True)
        request.session = MagicMock()
        response = cp.common(request)
        self.assertIsNotNone(response)

        config = response['cfg']
        self.assertIsNotNone(config)
        self.assertEqual('FreedomBox', config.box_name)

        self.assertEqual('FreedomBox', response['box_name'])

        submenu = response['submenu']
        self.assertIsNone(submenu)

        urls = response['active_menu_urls']
        self.assertIsNotNone(urls)
        self.assertEqual(['/', '/aaa/', '/aaa/bbb/', '/aaa/bbb/ccc/'], urls)

        self.assertTrue(response['user_is_admin'])

    def test_common_border_conditions(self):
        """Verify that the common() function works for border conditions."""
        request = HttpRequest()
        request.path = ''
        request.user = Mock()
        request.user.groups.filter().exists = Mock(return_value=True)
        request.session = MagicMock()
        response = cp.common(request)
        self.assertEqual([], response['active_menu_urls'])

        request.path = '/'
        response = cp.common(request)
        self.assertEqual(['/'], response['active_menu_urls'])

        request.path = '/aaa/bbb'
        response = cp.common(request)
        self.assertEqual(['/', '/aaa/'], response['active_menu_urls'])
