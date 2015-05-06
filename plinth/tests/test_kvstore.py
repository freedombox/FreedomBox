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

from django.test import TestCase

from plinth import kvstore


class KvstoreTestCase(TestCase):
    """Verify the behavior of the kvstore module."""

    def test_get(self):
        """Verify that a set value can be retrieved."""
        key = 'name'
        expected_value = 'Guido'
        kvstore.set(key, expected_value)
        actual_value = kvstore.get(key)
        self.assertEqual(expected_value, actual_value)

    def test_get_default(self):
        """Verify that either a set value or its default can be retrieved."""
        expected = 'default'
        actual = kvstore.get_default('bad_key', expected)
        self.assertEqual(expected, actual)
