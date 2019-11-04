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
Test module for key/value store.
"""

import pytest

from plinth import kvstore

pytestmark = pytest.mark.django_db


def test_get_set():
    """Verify that a set value can be retrieved."""
    key = 'name'
    expected_value = 'Guido'
    kvstore.set(key, expected_value)
    actual_value = kvstore.get(key)
    assert expected_value == actual_value


def test_get_set_complex_structures():
    """Verify that complex structures can be stored and retrieved."""
    key = 'compex_structure'
    expected_value = {
        'k1': 1,
        'k2': [2, 3],
        'k3': 4.5,
        'k4': 'Hello',
        'k5': {
            'a': 'b'
        }
    }
    kvstore.set(key, expected_value)
    actual_value = kvstore.get(key)
    assert expected_value == actual_value


def test_get_default():
    """Verify that either a set value or its default can be retrieved."""
    expected = 'default'
    actual = kvstore.get_default('bad_key', expected)
    assert expected == actual
