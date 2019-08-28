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

import abc
import io
import json
import logging
import os
from uuid import uuid1

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.errors import ActionError

from . import (ROOT_REPOSITORY, ROOT_REPOSITORY_NAME, ROOT_REPOSITORY_UUID,
               _backup_handler, api, get_known_hosts_path,
               restore_archive_handler, store)
from .errors import BorgError, BorgRepositoryDoesNotExistError, SshfsError

logger = logging.getLogger(__name__)

SUPPORTED_BORG_ENCRYPTION = ['none', 'repokey']
# known errors that come up when remotely accessing a borg repository
# 'errors' are error strings to look for in the stacktrace.
KNOWN_ERRORS = [{
    'errors': ['subprocess.TimeoutExpired'],
    'message':
        _('Connection refused - make sure you provided correct '
          'credentials and the server is running.'),
    'raise_as':
        BorgError,
},
                {
                    'errors': ['Connection refused'],
                    'message': _('Connection refused'),
                    'raise_as': BorgError,
                },
                {
                    'errors': [
                        'not a valid repository', 'does not exist',
                        'FileNotFoundError'
                    ],
                    'message':
                        _('Repository not found'),
                    'raise_as':
                        BorgRepositoryDoesNotExistError,
                },
                {
                    'errors': [('passphrase supplied in BORG_PASSPHRASE or by '
                                'BORG_PASSCOMMAND is incorrect')],
                    'message':
                        _('Incorrect encryption passphrase'),
                    'raise_as':
                        BorgError,
                },
                {
                    'errors': [('Connection reset by peer')],
                    'message': _('SSH access denied'),
                    'raise_as': SshfsError,
                }]


class BaseBorgRepository(abc.ABC):
    """Base class for all kinds of Borg repositories."""
    flags = {}
    is_mounted = True

    def __init__(self, uuid=None, path=None, credentials=None, **kwargs):
        """
        Instantiate a new repository.

        If only a uuid is given, load the values from kvstore.
        """
        self.kwargs = kwargs

        if not uuid:
            uuid = str(uuid1())
        self.uuid = uuid

        if path and credentials:
            self._path = path
            self.credentials = credentials
        else:
            # Either a uuid, or both a path and credentials must be given
            if not bool(uuid):
                raise ValueError('Invalid arguments.')
            else:
                self._load_from_kvstore()

    @property
    def name(self):
        """Return a display name for the repository."""
        return self._path

    @property
    def path(self):
        """Return the path of the repository."""
        return self._path

    @abc.abstractmethod
    def storage_type(self):
        """Return the storage type of repository."""
        raise NotImplementedError

    @staticmethod
    def is_usable():
        """Return whether the repository is ready to be used."""
        return True

    @property
    def borg_path(self):
        """Return the repository that the backups action script should use."""
        return self._path

    @staticmethod
    def _get_encryption_data(credentials):
        """Return additional dictionary data to send to backups call."""
        passphrase = credentials.get('encryption_passphrase', None)
        if passphrase:
            return {'encryption_passphrase': passphrase}

        return {}

    def _load_from_kvstore(self):
        storage = store.get(self.uuid)
        try:
            self.credentials = storage['credentials']
        except KeyError:
            self.credentials = {}
        self._path = storage['path']

    def get_info(self):
        """Return Borg information about a repository."""
        output = self.run(['info', '--path', self.borg_path])
        return json.loads(output)

    def get_view_content(self):
        """Get archives with additional information as needed by the view"""
        repository = {
            'uuid': self.uuid,
            'name': self.name,
            'storage_type': self.storage_type,
            'flags': self.flags,
            'error': None,
        }
        try:
            repository['mounted'] = self.is_mounted
            if repository['mounted']:
                repository['archives'] = self.list_archives()
        except (BorgError, ActionError) as err:
            repository['error'] = str(err)

        return repository

    def remove(self):
        """Remove a borg repository"""

    def list_archives(self):
        output = self.run(['list-repo', '--path', self.borg_path])
        archives = json.loads(output)['archives']
        return sorted(archives, key=lambda archive: archive['start'],
                      reverse=True)

    def create_archive(self, archive_name, app_names):
        archive_path = self._get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.backup_apps(_backup_handler, path=archive_path,
                        app_names=app_names, encryption_passphrase=passphrase)

    def delete_archive(self, archive_name):
        archive_path = self._get_archive_path(archive_name)
        self.run(['delete-archive', '--path', archive_path])

    def create_repository(self, encryption):
        """Initialize / create a borg repository."""
        if encryption not in SUPPORTED_BORG_ENCRYPTION:
            raise ValueError('Unsupported encryption: %s' % encryption)
        self.run(
            ['init', '--path', self.borg_path, '--encryption', encryption])

    def _run(self, cmd, arguments, superuser=True, **kwargs):
        """Run a backups or sshfs action script command."""
        try:
            if superuser:
                return actions.superuser_run(cmd, arguments, **kwargs)

            return actions.run(cmd, arguments, **kwargs)
        except ActionError as err:
            self.reraise_known_error(err)

    def run(self, arguments, superuser=True):
        """Add credentials and run a backups action script command."""
        for key in self.credentials.keys():
            if key not in self.KNOWN_CREDENTIALS:
                raise ValueError('Unknown credentials entry: %s' % key)

        input_data = json.dumps(self._get_encryption_data(self.credentials))
        return self._run('backups', arguments, superuser=superuser,
                         input=input_data.encode())

    def get_download_stream(self, archive_name):
        """Return an stream of .tar.gz binary data for a backup archive."""

        class BufferedReader(io.BufferedReader):
            """Improve performance of buffered binary streaming.

            Django simply returns the iterator as a response for the WSGI app.
            CherryPy then iterates over this iterator and writes to HTTP
            response. This calls __next__ over the BufferedReader that is
            process.stdout. However, this seems to call readline() which looks
            for \n in binary data which leads to short unpredictably sized
            chunks which in turn lead to severe performance degradation. So,
            overwrite this and call read() which is better geared for handling
            binary data.

            """

            def __next__(self):
                """Override to call read() instead of readline()."""
                chunk = self.read(io.DEFAULT_BUFFER_SIZE)
                if not chunk:
                    raise StopIteration

                return chunk

        args = ['export-tar', '--path', self._get_archive_path(archive_name)]
        input_data = json.dumps(self._get_encryption_data(self.credentials))
        proc = self._run('backups', args, run_in_background=True)
        proc.stdin.write(input_data.encode())
        proc.stdin.close()
        return BufferedReader(proc.stdout)

    def _get_archive_path(self, archive_name):
        """Return full borg path for an archive."""
        return '::'.join([self.borg_path, archive_name])

    @staticmethod
    def reraise_known_error(err):
        """Look whether the caught error is known and reraise it accordingly"""
        caught_error = str(err)
        for known_error in KNOWN_ERRORS:
            for error in known_error['errors']:
                if error in caught_error:
                    raise known_error['raise_as'](known_error['message'])

        raise err

    def get_archive(self, name):
        for archive in self.list_archives():
            if archive['name'] == name:
                return archive
        return None

    def get_archive_apps(self, archive_name):
        """Get list of apps included in an archive."""
        archive_path = self._get_archive_path(archive_name)
        output = self.run(['get-archive-apps', '--path', archive_path])
        return output.splitlines()

    def restore_archive(self, archive_name, apps=None):
        archive_path = self._get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.restore_apps(restore_archive_handler, app_names=apps,
                         create_subvolume=False, backup_file=archive_path,
                         encryption_passphrase=passphrase)

    def _get_storage_format(self, store_credentials, verified):
        storage = {
            'path': self._path,
            'storage_type': self.storage_type,
            'added_by_module': 'backups',
            'verified': verified
        }
        if self.uuid:
            storage['uuid'] = self.uuid

        if store_credentials:
            storage['credentials'] = self.credentials

        return storage

    def save(self, store_credentials=True, verified=False):
        """Save the repository in store (kvstore).

        - store_credentials: Boolean whether credentials should be stored.

        """
        storage = self._get_storage_format(store_credentials, verified)
        self.uuid = store.update_or_add(storage)


class RootBorgRepository(BaseBorgRepository):
    """Borg repository on the root filesystem."""
    storage_type = 'root'
    name = ROOT_REPOSITORY_NAME
    borg_path = ROOT_REPOSITORY
    sort_order = 10
    is_mounted = True

    def __init__(self, path, credentials=None):
        """Initialize the repository object."""
        self.uuid = ROOT_REPOSITORY_UUID
        if credentials is None:
            credentials = {}

        self._path = path
        self.credentials = credentials

    def run(self, arguments):
        return self._run('backups', arguments)


class BorgRepository(BaseBorgRepository):
    """General Borg repository implementation."""
    KNOWN_CREDENTIALS = ['encryption_passphrase']
    storage_type = 'disk'
    sort_order = 20
    flags = {'removable': True}

    @property
    def name(self):
        # TODO Use disk label as the name
        # Also, name isn't being used yet
        return self._path

    def remove(self):
        """Remove a repository from the kvstore."""
        store.delete(self.uuid)


class SshBorgRepository(BaseBorgRepository):
    """Borg repository that is accessed via SSH"""
    SSHFS_MOUNTPOINT = '/media/'
    KNOWN_CREDENTIALS = [
        'ssh_keyfile', 'ssh_password', 'encryption_passphrase'
    ]
    storage_type = 'ssh'
    sort_order = 30
    flags = {'removable': True, 'mountable': True}

    def is_usable(self):
        """Return whether repository is usable."""
        return self.kwargs.get('verified')

    @property
    def borg_path(self):
        """Return the path to use for backups actions.

        This is the mount point for the remote SSH repositories.

        """
        return self._mountpoint

    @property
    def mountpoint(self):
        """Return the local mount point where repository is to be mounted."""
        return os.path.join(self.SSHFS_MOUNTPOINT, self.uuid)

    @property
    def is_mounted(self):
        """Return whether remote path is mounted locally."""
        output = self._run('sshfs',
                           ['is-mounted', '--mountpoint', self.mountpoint])
        return json.loads(output)

    def mount(self):
        """Mount the remote path locally using sshfs."""
        if self.is_mounted:
            return
        known_hosts_path = get_known_hosts_path()
        arguments = [
            'mount', '--mountpoint', self.mountpoint, '--path', self._path,
            '--user-known-hosts-file',
            str(known_hosts_path)
        ]
        arguments, kwargs = self._append_sshfs_arguments(
            arguments, self.credentials)
        self._run('sshfs', arguments, **kwargs)

    def umount(self):
        """Unmount the remote path that was mounted locally using sshfs."""
        if not self.is_mounted:
            return

        self._run('sshfs', ['umount', '--mountpoint', self.mountpoint])

    def remove(self):
        """Remove a repository from the kvstore and delete its mountpoint"""
        self.umount()
        store.delete(self.uuid)
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

    @staticmethod
    def _append_sshfs_arguments(arguments, credentials):
        """Add credentials to a run command and kwargs"""
        kwargs = {}

        if 'ssh_password' in credentials and credentials['ssh_password']:
            kwargs['input'] = credentials['ssh_password'].encode()

        if 'ssh_keyfile' in credentials and credentials['ssh_keyfile']:
            arguments += ['--ssh-keyfile', credentials['ssh_keyfile']]

        return (arguments, kwargs)


def get_repositories():
    """Get all repositories of a given storage type."""
    repositories = [create_repository(ROOT_REPOSITORY_UUID)]
    for uuid in store.get_storages():
        repositories.append(create_repository(uuid))

    return sorted(repositories, key=lambda x: x.sort_order)


def create_repository(uuid):
    """Create a local or SSH repository object instance."""
    if uuid == ROOT_REPOSITORY_UUID:
        return RootBorgRepository(path=ROOT_REPOSITORY)

    storage = store.get(uuid)
    if storage['storage_type'] == 'ssh':
        return SshBorgRepository(uuid=uuid)

    return BorgRepository(uuid=uuid)
