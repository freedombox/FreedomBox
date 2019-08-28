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
