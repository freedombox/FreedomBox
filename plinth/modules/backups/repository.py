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
Remote and local Borg backup repositories
"""

import json
import logging
import os
from uuid import uuid1

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.errors import ActionError

from . import api, network_storage, _backup_handler, ROOT_REPOSITORY_NAME, \
        ROOT_REPOSITORY_UUID, ROOT_REPOSITORY, restore_archive_handler, \
        zipstream
from .errors import BorgError, BorgRepositoryDoesNotExistError, SshfsError

logger = logging.getLogger(__name__)

SSHFS_MOUNTPOINT = '/media/'
SUPPORTED_BORG_ENCRYPTION = ['none', 'repokey']
# known errors that come up when remotely accessing a borg repository
# 'errors' are error strings to look for in the stacktrace.
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
    },
    {
        "errors": [("passphrase supplied in BORG_PASSPHRASE or by "
                    "BORG_PASSCOMMAND is incorrect")],
        "message": _("Incorrect encryption passphrase"),
        "raise_as": BorgError,
    },
    {
        "errors": [("Connection reset by peer")],
        "message": _("SSH access denied"),
        "raise_as": SshfsError,
    }]


class BorgRepository(object):
    """Borg repository on the root filesystem"""
    storage_type = 'root'
    name = ROOT_REPOSITORY_NAME
    is_mounted = True

    def __init__(self, path, credentials={}):
        self._path = path
        self.credentials = credentials

    def append_credentials(self, arguments):
        """Append '--encryption-passphrase' argument to backups call"""
        passphrase = self.credentials.get('encryption_passphrase', None)
        if passphrase:
            arguments += ['--encryption-passphrase', passphrase]
        return arguments

    @property
    def repo_path(self):
        """Return the repository that the backups action script should use."""
        return self._path

    def get_info(self):
        output = self.run(['info', '--path', self.repo_path])
        return json.loads(output)

    def list_archives(self):
        output = self.run(['list-repo', '--path', self.repo_path])
        archives = json.loads(output)['archives']
        return sorted(archives, key=lambda archive: archive['start'],
                      reverse=True)

    def get_view_content(self):
        """Get archives with additional information as needed by the view"""
        repository = {
            'name': self.name,
            'type': self.storage_type,
            'error': ''
        }
        try:
            error = ''
            repository['mounted'] = self.is_mounted
            if repository['mounted']:
                repository['archives'] = self.list_archives()
        except (BorgError, ActionError) as \
                err:
            error = str(err)
        repository['error'] = error
        return repository

    def delete_archive(self, archive_name):
        archive_path = self.get_archive_path(archive_name)
        self.run(['delete-archive', '--path', archive_path])

    def remove_repository(self):
        """Remove a borg repository"""
        raise NotImplementedError

    def create_archive(self, archive_name, app_names):
        archive_path = self.get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.backup_apps(_backup_handler, path=archive_path,
                        app_names=app_names, encryption_passphrase=passphrase)

    def create_repository(self):
        self.run(['init', '--path', self.repo_path, '--encryption', 'none'])

    def get_zipstream(self, archive_name):
        archive_path = self.get_archive_path(archive_name)
        args = ['export-tar', '--path', archive_path]
        args = self.append_credentials(args)
        kwargs = {'run_in_background': True,
                  'bufsize': 1}
        proc = self._run('backups', args, kwargs=kwargs)
        return zipstream.ZipStream(proc.stdout, 'readline')

    def get_archive(self, name):
        for archive in self.list_archives():
            if archive['name'] == name:
                return archive

        return None

    def get_archive_apps(self, archive_name):
        """Get list of apps included in an archive."""
        archive_path = self.get_archive_path(archive_name)
        output = self.run(['get-archive-apps', '--path', archive_path])
        return output.splitlines()

    def restore_archive(self, archive_name, apps=None):
        archive_path = self.get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.restore_apps(restore_archive_handler, app_names=apps,
                         create_subvolume=False, backup_file=archive_path,
                         encryption_passphrase=passphrase)

    def get_archive_path(self, archive_name):
        return "::".join([self.repo_path, archive_name])

    def _run(self, cmd, arguments, superuser=True, kwargs=None):
        """Run a backups or sshfs action script command."""
        if kwargs is None:
            kwargs = {}
        try:
            if superuser:
                return actions.superuser_run(cmd, arguments, **kwargs)
            else:
                return actions.run(cmd, arguments, **kwargs)
        except ActionError as err:
            self.reraise_known_error(err)

    def run(self, arguments):
        return self._run('backups', arguments)

    def reraise_known_error(self, err):
        """Look whether the caught error is known and reraise it accordingly"""
        caught_error = str(err)
        for known_error in KNOWN_ERRORS:
            for error in known_error["errors"]:
                if error in caught_error:
                    raise known_error["raise_as"](known_error["message"])
        else:
            raise err


class SshBorgRepository(BorgRepository):
    """Borg repository that is accessed via SSH"""
    KNOWN_CREDENTIALS = ['ssh_keyfile', 'ssh_password',
                         'encryption_passphrase']
    storage_type = 'ssh'
    uuid = None

    def __init__(self, uuid=None, path=None, credentials=None, automount=True,
                 **kwargs):
        """
        Provide a uuid to instanciate an existing repository,
        or 'ssh_path' and 'credentials' for a new repository.
        """
        is_new_instance = not bool(uuid)
        if not uuid:
            uuid = str(uuid1())
        self.uuid = uuid

        if path and credentials:
            self._path = path
            self.credentials = credentials
        else:
            if is_new_instance:
                # Either a uuid, or both a path and credentials must be given
                raise ValueError('Invalid arguments.')
            else:
                self._load_from_kvstore()

        if automount:
            self.mount()

    @property
    def repo_path(self):
        """
        Return the path to use for backups actions.

        This is either the mountpoint or the remote ssh path,
        depending on whether borg is running on the remote server.
        """
        return self.mountpoint

    @property
    def mountpoint(self):
        return os.path.join(SSHFS_MOUNTPOINT, self.uuid)

    @property
    def name(self):
        return self._path

    @property
    def is_mounted(self):
        output = self._run('sshfs', ['is-mounted', '--mountpoint',
                                     self.mountpoint])
        return json.loads(output)

    def get_archive_path(self, archive_name):
        return "::".join([self.mountpoint, archive_name])

    def _load_from_kvstore(self):
        storage = network_storage.get(self.uuid)
        try:
            self.credentials = storage['credentials']
        except KeyError:
            self.credentials = {}
        self._path = storage['path']

    def _get_network_storage_format(self, store_credentials):
        storage = {
            'path': self._path,
            'storage_type': self.storage_type,
            'added_by_module': 'backups'
        }
        if self.uuid:
            storage['uuid'] = self.uuid
        if store_credentials:
            storage['credentials'] = self.credentials
        return storage

    def create_repository(self, encryption):
        """Initialize / create a borg repository."""
        if encryption not in SUPPORTED_BORG_ENCRYPTION:
            raise ValueError('Unsupported encryption: %s' % encryption)
        self.run(['init', '--path', self.repo_path, '--encryption',
                  encryption])

    def save(self, store_credentials=True):
        """
        Save the repository in network_storage (kvstore).
        - store_credentials: Boolean whether credentials should be stored.
        """
        storage = self._get_network_storage_format(store_credentials)
        self.uuid = network_storage.update_or_add(storage)

    def mount(self):
        if self.is_mounted:
            return

        arguments = ['mount', '--mountpoint', self.mountpoint, '--path',
                     self._path]
        arguments, kwargs = self._append_sshfs_arguments(arguments,
                                                         self.credentials)
        self._run('sshfs', arguments, kwargs=kwargs)

    def umount(self):
        if not self.is_mounted:
            return
        self._run('sshfs', ['umount', '--mountpoint', self.mountpoint])

    def remove_repository(self):
        """Remove a repository from the kvstore and delete its mountpoint"""
        network_storage.delete(self.uuid)
        try:
            if os.path.exists(self.mountpoint):
                try:
                    self.umount()
                except ActionError:
                    pass
                if not os.listdir(self.mountpoint):
                    os.rmdir(self.mountpoint)
        except Exception as err:
            logger.error(err)

    def _append_sshfs_arguments(self, arguments, credentials, kwargs=None):
        if kwargs is None:
            kwargs = {}
        if 'ssh_password' in credentials and credentials['ssh_password']:
            kwargs['input'] = credentials['ssh_password'].encode()
        if 'ssh_keyfile' in credentials and credentials['ssh_keyfile']:
            arguments += ['--ssh-keyfile', credentials['ssh_keyfile']]
        return (arguments, kwargs)

    def _append_run_arguments(self, arguments, credentials):
        kwargs = {}
        passphrase = credentials.get('encryption_passphrase', None)
        if passphrase:
            arguments += ['--encryption-passphrase', passphrase]
        # TODO: use or remove
        """
        if 'ssh_password' in credentials and credentials['ssh_password']:
            kwargs['input'] = credentials['ssh_password'].encode()
        if 'ssh_keyfile' in credentials and credentials['ssh_keyfile']:
            arguments += ['--ssh-keyfile', credentials['ssh_keyfile']]
        """
        return (arguments, kwargs)

    def run(self, arguments, superuser=True):
        """Run a backups action script command.

        Add credentials via self._append_run_arguments to the backup script.
        """
        for key in self.credentials.keys():
            if key not in self.KNOWN_CREDENTIALS:
                raise ValueError('Unknown credentials entry: %s' % key)
        arguments = self.append_credentials(arguments)
        return self._run('backups', arguments, superuser=superuser)


def get_ssh_repositories():
    """Get all SSH Repositories including the archive content"""
    repositories = {}
    for storage in network_storage.get_storages().values():
        repository = SshBorgRepository(automount=False, **storage)
        repositories[storage['uuid']] = repository.get_view_content()
    return repositories


def get_repository(uuid):
    """Get a repository (BorgRepository or SshBorgRepository)"""
    if uuid == ROOT_REPOSITORY_UUID:
        return BorgRepository(path=ROOT_REPOSITORY)
    else:
        return SshBorgRepository(uuid=uuid, automount=False)
