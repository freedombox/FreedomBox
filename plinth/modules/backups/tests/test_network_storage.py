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

from django.test import TestCase

from plinth.modules.backups import network_storage


class TestNetworkStorage(TestCase):
    """Test handling network storage in kvstore"""
    storages = [{
        'path': 'test@nonexistent.org:~/',
        'storage_type': 'ssh',
        'added_by_module': 'test'
    }, {
        'path': 'test@nonexistent.org:~/tmp/repo/',
        'storage_type': 'ssh',
        'added_by_module': 'test'
    }]

    def test_add(self):
        """Add a storage item"""
        storage = self.storages[0]
        uuid = network_storage.update_or_add(storage)
        _storage = network_storage.get(uuid)
        self.assertEqual(_storage['path'], storage['path'])

    def test_add_invalid(self):
        """Add a storage item"""
        storage_with_missing_type = {
            'path': 'test@nonexistent.org:~/tmp/repo/',
            'added_by_module': 'test'
        }
        with self.assertRaises(ValueError):
            network_storage.update_or_add(storage_with_missing_type)

    def test_remove(self):
        """Add and remove storage items"""
        storage = self.storages[0]
        uuid = None
        for storage in self.storages:
            uuid = network_storage.update_or_add(storage)
        storages = network_storage.get_storages()
        self.assertEqual(len(storages), 2)
        network_storage.delete(uuid)
        storages = network_storage.get_storages()
        self.assertEqual(len(storages), 1)

    def test_update(self):
        """Update existing storage items"""
        uuid = None
        for storage in self.storages:
            uuid = network_storage.update_or_add(storage)
        storage = network_storage.get(uuid)
        new_path = 'test@nonexistent.org:~/tmp/repo_new/'
        storage['path'] = new_path
        network_storage.update_or_add(storage)
        _storage = network_storage.get(uuid)
        self.assertEquals(_storage['path'], new_path)
