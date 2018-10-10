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

import json
import os

from django.utils.text import get_valid_filename
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu

from . import api

version = 1

managed_packages = ['borgbackup']

name = _('Backups')

description = [
    _('Backups allows creating and managing backup archives.'),
]

service = None

MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'
REPOSITORY = '/var/lib/freedombox/borgbackup'
SESSION_BACKUP_VARIABLE = 'fbx-backup-filestamp'
# default backup path for temporary actions like imports or download
TMP_BACKUP_PATH = '/tmp/freedombox-backup.tar.gz'
# session variable name that stores when a backup file should be deleted


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
        'name': app.name,
        'version': app.app.version,
        'backup': app.manifest
    } for app in packet.apps]
    with open(manifest_path, 'w') as manifest_file:
        json.dump(manifests, manifest_file)

    paths = packet.directories + packet.files
    paths.append(manifest_path)
    actions.superuser_run(
        'backups', ['create', '--name', packet.label, '--paths'] + paths)


def create_archive(name, app_names):
    api.backup_apps(_backup_handler, app_names, name)


def delete_archive(name):
    # TODO: is name actually a path?
    actions.superuser_run('backups', ['delete', '--name', name])


def delete_tmp_backup_file():
    if os.path.isfile(TMP_BACKUP_PATH):
        os.remove(TMP_BACKUP_PATH)


def export_archive(name, filepath=TMP_BACKUP_PATH):
    arguments = ['export-tar', '--archive', name, '--filepath', filepath]
    actions.superuser_run('backups', arguments)


def get_archive_path(archive_name):
    """Get path of an archive"""
    return "::".join([REPOSITORY, archive_name])


def get_archive_apps(path):
    """Get list of apps included in an archive."""
    output = actions.superuser_run('backups',
                                   ['get-archive-apps', '--path', path])
    return output.splitlines()


def get_apps_of_exported_archive(path):
    """Get list of apps included in exported archive file."""
    arguments = ['get-apps-of-exported-archive', '--path', path]
    output = actions.superuser_run('backups', arguments)
    return output.splitlines()


def _restore_exported_archive_handler(packet):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups', ['restore-exported-archive',
        '--path', packet.label], input=locations_data.encode())


def _restore_archive_handler(packet):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups', ['restore-archive', '--path',
                packet.label, '--destination', '/'], input=locations_data.encode())


def restore_from_tmp(apps=None):
    """Restore files from temporary backup file"""
    api.restore_apps(_restore_exported_archive_handler, app_names=apps,
                     create_subvolume=False, backup_file=TMP_BACKUP_PATH)


def restore(archive_path, apps=None):
    """Restore files from a backup archive."""
    api.restore_apps(_restore_archive_handler, app_names=apps,
                     create_subvolume=False, backup_file=archive_path)
