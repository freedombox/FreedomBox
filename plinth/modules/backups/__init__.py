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

from plinth import actions, cfg
from plinth.menu import main_menu
from plinth.utils import format_lazy

from . import api

version = 1

managed_packages = ['borgbackup', 'sshfs']

name = _('Backups')

description = [
    _('Backups allows creating and managing backup archives.'),
]

service = None

MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'
ROOT_REPOSITORY = '/var/lib/freedombox/borgbackup'
ROOT_REPOSITORY_NAME = format_lazy(_('{box_name} storage'),
                                   box_name=cfg.box_name)
# session variable name that stores when a backup file should be deleted
SESSION_PATH_VARIABLE = 'fbx-backups-upload-path'


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-duplicate', 'backups:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'backups', ['setup', '--path',
                                                           ROOT_REPOSITORY])


def _backup_handler(packet):
    """Performs backup operation on packet."""
    if not os.path.exists(MANIFESTS_FOLDER):
        os.makedirs(MANIFESTS_FOLDER)

    manifest_path = os.path.join(MANIFESTS_FOLDER,
                                 get_valid_filename(packet.label) + '.json')
    manifests = {
        'apps': [{
            'name': app.name,
            'version': app.app.version,
            'backup': app.manifest
        } for app in packet.apps]
    }
    with open(manifest_path, 'w') as manifest_file:
        json.dump(manifests, manifest_file)

    paths = packet.directories + packet.files
    paths.append(manifest_path)
    actions.superuser_run(
        'backups', ['create-archive', '--name', packet.label, '--paths'] +
        # TODO: add ssh_keyfile
        paths)


def get_exported_archive_apps(path):
    """Get list of apps included in exported archive file."""
    arguments = ['get-exported-archive-apps', '--path', path]
    output = actions.superuser_run('backups', arguments)
    return output.splitlines()


def _restore_exported_archive_handler(packet):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups', ['restore-exported-archive', '--path',
                                      packet.label],
                          input=locations_data.encode())


def _restore_archive_handler(packet):
    """Perform restore operation on packet."""
    locations = {'directories': packet.directories, 'files': packet.files}
    locations_data = json.dumps(locations)
    actions.superuser_run('backups', ['restore-archive', '--path',
                                      packet.label, '--destination', '/'],
                          input=locations_data.encode())


def restore_from_upload(path, apps=None):
    """Restore files from an uploaded .tar.gz backup file"""
    api.restore_apps(_restore_exported_archive_handler, app_names=apps,
                     create_subvolume=False, backup_file=path)


def restore(archive_path, apps=None):
    """Restore files from a backup archive."""
    api.restore_apps(_restore_archive_handler, app_names=apps,
                     create_subvolume=False, backup_file=archive_path)
