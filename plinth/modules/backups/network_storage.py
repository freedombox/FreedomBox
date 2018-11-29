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
Manage remote (network) storage storages in plinths' KVStore.
"""

import json
from uuid import uuid1

from plinth import kvstore

# kvstore key for network storage
NETWORK_STORAGE_KEY = 'network_storage'
REQUIRED_FIELDS = ['path', 'storage_type', 'added_by_module']


def get_storages(storage_type=None):
    """Get list of network storage storages"""
    storages = kvstore.get_default(NETWORK_STORAGE_KEY, [])
    if storages:
        storages = json.loads(storages)
    if storage_type:
        storages = [storage for storage in storages if 'type' in storage
                    and storage['type'] == storage_type]
    return storages


def get(uuid):
    storages = get_storages()
    return list(filter(lambda storage: storage['uuid'] == uuid,
                       storages))[0]


def update_or_add(storage):
    """Update an existing or create a new network location"""
    for field in REQUIRED_FIELDS:
        assert field in storage
    storages = get_storages()
    if 'uuid' in storage:
        # Replace the existing storage
        storages = [_storage if _storage['uuid'] != storage['uuid'] else
                    storage for _storage in storages]
    else:
        storage['uuid'] = str(uuid1())
        storages.append(storage)
    kvstore.set(NETWORK_STORAGE_KEY, json.dumps(storages))


def delete(uuid):
    """Remove a network storage from kvstore"""
    storages = get_storages()
    storages = list(filter(lambda storage: storage['uuid'] != uuid,
                           storages))
    kvstore.set(NETWORK_STORAGE_KEY, json.dumps(storages))
