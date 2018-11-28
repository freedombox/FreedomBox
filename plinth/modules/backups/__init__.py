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
from plinth.errors import ActionError
from .errors import BorgError, BorgRepositoryDoesNotExistError

from . import api

version = 1

managed_packages = ['borgbackup', 'sshfs']

name = _('Backups')

description = [
    _('Backups allows creating and managing backup archives.'),
]

service = None

MANIFESTS_FOLDER = '/var/lib/plinth/backups-manifests/'
REPOSITORY = '/var/lib/freedombox/borgbackup'
# session variable name that stores when a backup file should be deleted
SESSION_PATH_VARIABLE = 'fbx-backups-upload-path'
# known errors that come up when remotely accessing a borg repository
# 'errors' are error strings to look for in the stacktrace.
ACCESS_PARAMS = ['ssh_keyfile', 'ssh_password', 'encryption_passphrase']
# kvstore key for storing remote locations
REMOTE_LOCATIONS_KEY = 'remote_locations'
KNOWN_ERRORS = [{
        "errors": ["subprocess.TimeoutExpired"],
        "message": _("Connection refused - make sure you provided correct "
                     "credentials and the server is running."),
        "raise_as": BorgError,
    },
    {
        "errors": ["Connection refused"],
        "message": _("Connection refused"),
        "raise_as": BorgError,
    },
    {
        "errors": ["not a valid repository", "does not exist"],
        "message": _("Repository not found"),
        "raise_as": BorgRepositoryDoesNotExistError,
    }]


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-duplicate', 'backups:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'backups', ['setup'])


def get_info(repository, access_params=None):
    cmd = ['info', '--repository', repository]
    output = run(cmd, access_params)
    return json.loads(output)


def list_archives(repository, access_params=None):
    try:
        output = run(['list-repo', '--path', repository], access_params)
    except ActionError as err:
        reraise_known_error(err)
    else:
        return json.loads(output)['archives']


def get_archive(name):
    # TODO: can't we get this archive directly?
    for archive in list_archives():
        if archive['name'] == name:
            return archive

    return None


def reraise_known_error(err):
    """Look whether the caught error is known and re-raise it accordingly"""
    caught_error = str(err)
    for known_error in KNOWN_ERRORS:
        for error in known_error["errors"]:
            if error in caught_error:
                raise known_error["raise_as"](known_error["message"])
    else:
        raise err


def test_connection(repository, access_params=None):
    """
    Test connecting to a local or remote borg repository.
    Tries to detect (and throw) some known ssh or borg errors.
    Returns 'borg info' information otherwise.
    """
    try:
        return get_info(repository, access_params)
    except ActionError as err:
        reraise_known_error(err)


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


def create_archive(name, app_names, access_params=None):
    api.backup_apps(_backup_handler, app_names, name,
                    access_params=access_params)


def create_repository(repository, encryption, access_params=None):
    cmd = ['init', '--repository', repository, '--encryption', encryption]
    run(cmd, access_params=access_params)


def delete_archive(path):
    actions.superuser_run('backups', ['delete-archive', '--path', path])


def get_archive_path(archive_name):
    """Get path of an archive"""
    return "::".join([REPOSITORY, archive_name])


def get_archive_apps(path):
    """Get list of apps included in an archive."""
    output = actions.superuser_run('backups',
                                   ['get-archive-apps', '--path', path])
    return output.splitlines()


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


def get_args(params):
    args = []
    kwargs = {}
    if 'ssh_password' in params and params['ssh_password'] is not None:
        kwargs['input'] = params['ssh_password'].encode()
    if 'ssh_keyfile' in params and params['ssh_keyfile'] is not None:
        args += ['--ssh-keyfile', params['ssh_keyfile']]
    if 'encryption_passphrase' in params and \
       params['encryption_passphrase'] is not None:
        args += ['--encryption-passphrase', params['encryption_passphrase']]
    return (args, kwargs)


def run(arguments, access_params=None, superuser=True):
    """Run a given command, appending (kw)args as necessary"""
    command = 'backups'
    kwargs = {}
    if access_params:
        for key in access_params.keys():
            if key not in ACCESS_PARAMS:
                raise ValueError('Unknown access parameter: %s' % key)

        append_arguments, kwargs = get_args(access_params)
        arguments += append_arguments

    if superuser:
        return actions.superuser_run(command, arguments, **kwargs)
    else:
        return actions.run(command, arguments, **kwargs)
