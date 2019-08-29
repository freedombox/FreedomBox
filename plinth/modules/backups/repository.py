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
import contextlib
import io
import json
import logging
import os
import re
from uuid import uuid1

import paramiko
from django.utils.translation import ugettext_lazy as _

from plinth import actions, cfg
from plinth.errors import ActionError
from plinth.utils import format_lazy

from . import (_backup_handler, api, errors, get_known_hosts_path,
               restore_archive_handler, split_path, store)

logger = logging.getLogger(__name__)

# known errors that come up when remotely accessing a borg repository
# 'errors' are error strings to look for in the stacktrace.
KNOWN_ERRORS = [
    {
        'errors': ['subprocess.TimeoutExpired'],
        'message':
            _('Connection refused - make sure you provided correct '
              'credentials and the server is running.'),
        'raise_as':
            errors.BorgError,
    },
    {
        'errors': ['Connection refused'],
        'message': _('Connection refused'),
        'raise_as': errors.BorgError,
    },
    {
        'errors': [
            'not a valid repository', 'does not exist', 'FileNotFoundError'
        ],
        'message':
            _('Repository not found'),
        'raise_as':
            errors.BorgRepositoryDoesNotExistError,
    },
    {
        'errors': ['passphrase supplied in .* is incorrect'],
        'message': _('Incorrect encryption passphrase'),
        'raise_as': errors.BorgError,
    },
    {
        'errors': ['Connection reset by peer'],
        'message': _('SSH access denied'),
        'raise_as': errors.SshfsError,
    },
    {
        'errors': ['There is already something at'],
        'message':
            _('Repository path is neither empty nor '
              'is an existing backups repository.'),
        'raise_as':
            errors.BorgError,
    },
    {
        'errors': ['A repository already exists at'],
        'message': None,
        'raise_as': errors.BorgRepositoryExists,
    },
]


class BaseBorgRepository(abc.ABC):
    """Base class for all kinds of Borg repositories."""
    flags = {}
    is_mounted = True
    known_credentials = []

    def __init__(self, path, credentials=None, uuid=None, **kwargs):
        """Instantiate a new repository.

        If only a uuid is given, load the values from kvstore.

        """
        self._path = path
        self.credentials = credentials or {}
        self.uuid = uuid or str(uuid1())
        self.kwargs = kwargs

    @classmethod
    def load(cls, uuid):
        """Create instance by loading from database."""
        storage = dict(store.get(uuid))
        path = storage.pop('path')
        storage.pop('uuid')
        credentials = storage.setdefault('credentials', {})
        storage.pop('credentials')

        return cls(path, credentials, uuid, **storage)

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
        except (errors.BorgError, ActionError) as err:
            repository['error'] = str(err)

        return repository

    def remove(self):
        """Remove a borg repository"""

    def list_archives(self):
        """Return list of archives in this repository."""
        output = self.run(['list-repo', '--path', self.borg_path])
        archives = json.loads(output)['archives']
        return sorted(archives, key=lambda archive: archive['start'],
                      reverse=True)

    def create_archive(self, archive_name, app_names):
        """Create a new archive in this repository with given name."""
        archive_path = self._get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.backup_apps(_backup_handler, path=archive_path,
                        app_names=app_names, encryption_passphrase=passphrase)

    def delete_archive(self, archive_name):
        """Delete an archive with given name from this repository."""
        archive_path = self._get_archive_path(archive_name)
        self.run(['delete-archive', '--path', archive_path])

    def initialize(self):
        """Initialize / create a borg repository."""
        encryption = 'none'
        if 'encryption_passphrase' in self.credentials and \
           self.credentials['encryption_passphrase']:
            encryption = 'repokey'

        try:
            self.run(
                ['init', '--path', self.borg_path, '--encryption', encryption])
        except errors.BorgRepositoryExists:
            pass

        self.get_info()  # If password is incorrect raise an error early.

    @staticmethod
    def _get_encryption_data(credentials):
        """Return additional dictionary data to send to backups call."""
        passphrase = credentials.get('encryption_passphrase', None)
        if passphrase:
            return {'encryption_passphrase': passphrase}

        return {}

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
            if key not in self.known_credentials:
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
                if re.search(error, caught_error):
                    raise known_error['raise_as'](known_error['message'])

        raise err

    def get_archive(self, name):
        """Return a specific archive from this repository with given name."""
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
        """Restore an archive from this repository to the system."""
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
    UUID = 'root'
    PATH = '/var/lib/freedombox/borgbackup'

    storage_type = 'root'
    name = format_lazy(_('{box_name} storage'), box_name=cfg.box_name)
    borg_path = PATH
    sort_order = 10
    is_mounted = True

    def __init__(self, credentials=None):
        """Initialize the repository object."""
        super().__init__(self.PATH, credentials, self.UUID)


class BorgRepository(BaseBorgRepository):
    """General Borg repository implementation."""
    known_credentials = ['encryption_passphrase']
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
    known_credentials = [
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
    def hostname(self):
        """Return hostname from the remote path."""
        _, hostname, _ = split_path(self._path)
        return hostname.split('%')[0]  # XXX: Likely incorrect to split

    @property
    def _mountpoint(self):
        """Return the local mount point where repository is to be mounted."""
        return os.path.join(self.SSHFS_MOUNTPOINT, self.uuid)

    @property
    def is_mounted(self):
        """Return whether remote path is mounted locally."""
        output = self._run('sshfs',
                           ['is-mounted', '--mountpoint', self._mountpoint])
        return json.loads(output)

    def initialize(self):
        """Initialize the repository after mounting the target directory."""
        self._ensure_remote_directory()
        self.mount()
        super().initialize()

    def mount(self):
        """Mount the remote path locally using sshfs."""
        if self.is_mounted:
            return
        known_hosts_path = get_known_hosts_path()
        arguments = [
            'mount', '--mountpoint', self._mountpoint, '--path', self._path,
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

        self._run('sshfs', ['umount', '--mountpoint', self._mountpoint])

    def remove(self):
        """Remove a repository from the kvstore and delete its mountpoint"""
        self.umount()
        store.delete(self.uuid)
        try:
            if os.path.exists(self._mountpoint):
                try:
                    self.umount()
                except ActionError:
                    pass
                if not os.listdir(self._mountpoint):
                    os.rmdir(self._mountpoint)
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

    def _ensure_remote_directory(self):
        """Create remote SSH directory if it does not exist."""
        username, hostname, dir_path = split_path(self.path)
        if dir_path == '':
            dir_path = '.'

        if dir_path[0] == '~':
            dir_path = '.' + dir_path[1:]

        password = self.credentials['ssh_password']

        # Ensure remote directory exists, check contents
        # TODO Test with IPv6 connection
        with _ssh_connection(hostname, username, password) as ssh_client:
            with ssh_client.open_sftp() as sftp_client:
                try:
                    sftp_client.listdir(dir_path)
                except FileNotFoundError:
                    logger.info('Directory %s does not exist, creating.',
                                dir_path)
                    sftp_client.mkdir(dir_path)


@contextlib.contextmanager
def _ssh_connection(hostname, username, password):
    """Context manager to create and close an SSH connection."""
    ssh_client = paramiko.SSHClient()
    ssh_client.load_host_keys(str(get_known_hosts_path()))

    try:
        ssh_client.connect(hostname, username=username, password=password)
        yield ssh_client
    finally:
        ssh_client.close()


def get_repositories():
    """Get all repositories of a given storage type."""
    repositories = [get_instance(RootBorgRepository.UUID)]
    for uuid in store.get_storages():
        repositories.append(get_instance(uuid))

    return sorted(repositories, key=lambda x: x.sort_order)


def get_instance(uuid):
    """Create a local or SSH repository object instance."""
    if uuid == RootBorgRepository.UUID:
        return RootBorgRepository()

    storage = store.get(uuid)
    if storage['storage_type'] == 'ssh':
        return SshBorgRepository.load(uuid)

    return BorgRepository.load(uuid)
