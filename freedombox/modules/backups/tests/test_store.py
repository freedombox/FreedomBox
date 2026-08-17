# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test network storage.
"""

import pytest

from plinth.modules.backups import store

pytestmark = pytest.mark.django_db

_storages = [
    {
        'path': 'test@nonexistent.org:~/',
        'storage_type': 'ssh',
        'added_by_module': 'test'
    },
    {
        'path': 'test@nonexistent.org:~/tmp/repo/',
        'storage_type': 'ssh',
        'added_by_module': 'test'
    },
]


def test_add():
    """Add a storage item"""
    storage = _storages[0]
    uuid = store.update_or_add(storage)
    _storage = store.get(uuid)
    assert _storage['path'] == storage['path']


def test_add_invalid():
    """Add a storage item"""
    storage_with_missing_type = {
        'path': 'test@nonexistent.org:~/tmp/repo/',
        'added_by_module': 'test'
    }
    with pytest.raises(ValueError):
        store.update_or_add(storage_with_missing_type)


def test_remove():
    """Add and remove storage items"""
    storage = _storages[0]
    uuid = None
    for storage in _storages:
        uuid = store.update_or_add(storage)

    storages = store.get_storages()
    assert len(storages) == 2
    store.delete(uuid)
    storages = store.get_storages()
    assert len(storages) == 1


def test_update():
    """Update existing storage items"""
    uuid = None
    for storage in _storages:
        uuid = store.update_or_add(storage)

    storage = store.get(uuid)
    new_path = 'test@nonexistent.org:~/tmp/repo_new/'
    storage['path'] = new_path
    store.update_or_add(storage)
    _storage = store.get(uuid)
    assert _storage['path'] == new_path
