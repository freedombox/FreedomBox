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
    """Get network storages"""
    storages = kvstore.get_default(NETWORK_STORAGE_KEY, {})
    if storages:
        storages = json.loads(storages)
    if storage_type:
        storages = {uuid: storage for uuid, storage in storages.items() if
                    storage['storage_type'] == storage_type}
    return storages


def get(uuid):
    storages = get_storages()
    return storages[uuid]


def update_or_add(storage):
    """Update an existing or create a new network storage"""
    for field in REQUIRED_FIELDS:
        if field not in storage:
            raise ValueError('missing storage parameter: %s' % field)
    existing_storages = get_storages()
    if 'uuid' in storage:
        # Replace the existing storage
        existing_storages[storage['uuid']] = storage
    else:
        uuid = str(uuid1())
        storage['uuid'] = uuid
        existing_storages[uuid] = storage
    kvstore.set(NETWORK_STORAGE_KEY, json.dumps(existing_storages))
    return storage['uuid']


def delete(uuid):
    """Remove a network storage from kvstore"""
    storages = get_storages()
    del storages[uuid]
    kvstore.set(NETWORK_STORAGE_KEY, json.dumps(storages))
