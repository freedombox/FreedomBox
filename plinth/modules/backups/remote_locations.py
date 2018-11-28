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
Manage remote storage locations
"""

import json
import logging
import os
from uuid import uuid1

from django.utils.translation import ugettext as _

from plinth import kvstore
from plinth.errors import ActionError

from . import sshfs, list_archives, reraise_known_error, REMOTE_LOCATIONS_KEY
from .errors import BorgError

logger = logging.getLogger(__name__)
MOUNTPOINT = '/media/'


def add(path, repotype, encryption, access_params, store_passwords, added_by):
    locations = get_locations()
    location = {
        'uuid': str(uuid1()),
        'path': path,
        'type': repotype,
        'encryption': encryption,
        'added_by': added_by
    }
    if store_passwords:
        if 'encryption_passphrase' in access_params:
            location['encryption_passphrase'] = \
                    access_params['encryption_passphrase']
        if 'ssh_password' in access_params:
            location['ssh_password'] = access_params['ssh_password']
    locations.append(location)
    kvstore.set(REMOTE_LOCATIONS_KEY, json.dumps(locations))


def delete(uuid):
    """Umount a location, remove it from kvstore and unlink the mountpoint"""
    locations = get_locations()
    location = get_location(uuid)
    mountpoint = os.path.join(MOUNTPOINT, location['uuid'])
    locations = list(filter(lambda location: location['uuid'] != uuid,
                            locations))
    kvstore.set(REMOTE_LOCATIONS_KEY, json.dumps(locations))
    if os.path.exists(mountpoint):
        try:
            sshfs.umount(mountpoint)
        except ActionError:
            pass
        try:
            os.unlink(mountpoint)
        except Exception as err:
            logger.error(err)


def get_archives(uuid=None):
    """
    Get archives of one or all locations.
    returns: {
        uuid: {
            'path': path,
            'type': type,
            'archives': [],
            'error': error_message
        }
    }
    """
    locations = {}
    for location in get_locations():
        mountpoint = os.path.join(MOUNTPOINT, location['uuid'])
        new_location = {
            'path': location['path'],
            'mounted': uuid_is_mounted(location['uuid']),
        }
        if new_location['mounted']:
            try:
                new_location['archives'] = list_archives(mountpoint)
            except BorgError as err:
                new_location['error'] = str(err)
            except Exception as err:
                logger.error(err)
                new_location['error'] = _("Access failed")
        locations[location['uuid']] = new_location

    return locations


def get_locations(location_type=None):
    """Get list of all locations"""
    # TODO: hold locations in memory?
    locations = kvstore.get_default(REMOTE_LOCATIONS_KEY, [])
    if locations:
        locations = json.loads(locations)
    if location_type:
        locations = [location for location in locations if 'type' in location
                     and location['type'] == location_type]
    return locations


def get_location(uuid):
    locations = get_locations()
    return list(filter(lambda location: location['uuid'] == uuid,
                       locations))[0]


def _mount_locations(uuid=None):
    locations = get_locations(location_type='ssh')
    for location in locations:
        _mount_location(location)


def _mount_location(location):
    # TODO: shouldn't I just store and query the access_params as they are?
    # but encryption_passphrase is not an ssh access_param..
    mountpoint = os.path.join(MOUNTPOINT, location['uuid'])
    is_mounted = False
    if sshfs.is_mounted(mountpoint):
        is_mounted = True
    else:
        access_params = _get_access_params(location)
        # TODO: use actual feedback of sshfs.mount
        try:
            sshfs.mount(location['path'], mountpoint, access_params)
        except Exception as err:
            reraise_known_error(err)
        is_mounted = True
    return is_mounted


def _umount_location(location):
    mountpoint = os.path.join(MOUNTPOINT, location['uuid'])
    return sshfs.umount(mountpoint)


def _get_access_params(location):
    keys = ['encryption_passphrase', 'ssh_keyfile', 'ssh_password']
    access_params = {key: location[key] for key in keys if key in location}
    if location['type'] == 'ssh':
        if 'ssh_keyfile' not in location and 'ssh_password' not in \
                location:
            raise ValueError('Missing credentials')
    return access_params


def mount_uuid(uuid):
    location = get_location(uuid)
    mounted = False
    if location:
        mounted = _mount_location(location)
    return mounted


def umount_uuid(uuid):
    location = get_location(uuid)
    return _umount_location(location)


def uuid_is_mounted(uuid):
    mountpoint = os.path.join(MOUNTPOINT, uuid)
    return sshfs.is_mounted(mountpoint)
