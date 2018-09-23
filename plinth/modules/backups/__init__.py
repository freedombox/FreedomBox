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
FreedomBox app to manage backup archives.
"""

import errno
import json
import os

from django.utils.text import get_valid_filename
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu
from plinth.modules import udiskie

from .backups import backup_apps, restore_apps

version = 1

managed_packages = ['borgbackup']

name = _('Backups')

description = [
    _('Backups allows creating and managing backup archives.'),
]

service = None

MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-duplicate', 'backups:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'backups', ['setup'])


def get_info():
    output = actions.superuser_run('backups', ['info'])
    return json.loads(output)


def list_archives():
    output = actions.superuser_run('backups', ['list'])
    return json.loads(output)['archives']


def get_archive(name):
    for archive in list_archives():
        if archive['name'] == name:
            return archive

    return None


def _backup_handler(packet):
    """Performs backup operation on packet."""
    if not os.path.exists(MANIFESTS_FOLDER):
        os.makedirs(MANIFESTS_FOLDER)

    manifest_path = os.path.join(MANIFESTS_FOLDER,
                                 get_valid_filename(packet.label) + '.json')
    manifests = [{
        'name': manifest[0],
        'version': manifest[1].version,
        'backup': manifest[2]
    } for manifest in packet.manifests]
    with open(manifest_path, 'w') as manifest_file:
        json.dump(manifests, manifest_file)

    paths = packet.directories + packet.files
    paths.append(manifest_path)
    actions.superuser_run(
        'backups', ['create', '--name', packet.label, '--paths'] + paths)


def create_archive(name, app_names):
    backup_apps(_backup_handler, app_names, name)


def delete_archive(name):
    actions.superuser_run('backups', ['delete', '--name', name])


def export_archive(name, location):
    if location[-1] != '/':
        location += '/'

    filename = location + 'FreedomBox-backups/' + get_valid_filename(
        name) + '.tar.gz'
    actions.superuser_run('backups',
                          ['export', '--name', name, '--filename', filename])


def get_export_locations():
    """Return a list of storage locations for exported backup archives."""
    locations = [('/var/lib/freedombox/', _('Root Filesystem'))]
    if udiskie.is_running():
        devices = udiskie.udisks2.list_devices()
        for device in devices:
            if 'mount_points' in device and len(device['mount_points']) > 0:
                name = device['label'] or device['device']
                locations.append((device['mount_points'][0], name))

    return locations


def get_export_files():
    """Return a dict of exported backup archives found in storage locations."""
    locations = get_export_locations()
    export_files = {}
    for location in locations:
        output = actions.superuser_run(
            'backups', ['list-exports', '--location', location[0]])
        export_files[location[1]] = json.loads(output)

    return export_files


def find_exported_archive(disk_label, archive_name):
    """Return the full path for the exported archive file."""
    locations = get_export_locations()
    for location in locations:
        if location[1] == disk_label:
            return os.path.join(location[0], 'FreedomBox-backups',
                                archive_name)

    raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                            archive_name)


def get_export_apps(filename):
    """Get list of apps included in exported archive file."""
    output = actions.superuser_run('backups',
                                   ['get-export-apps', '--filename', filename])
    return output.splitlines()


def _restore_handler(packet):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups', ['restore', '--filename', packet.label],
                          input=locations_data.encode())


def restore_exported(label, archive_name, apps=None):
    """Restore files from exported backup archive."""
    filename = find_exported_archive(label, archive_name)
    restore_apps(_restore_handler, app_names=apps, create_subvolume=False,
                 backup_file=filename)
