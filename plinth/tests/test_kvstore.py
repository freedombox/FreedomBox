# SPDX-License-Identifier: AGPL-3.0-or-later
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
