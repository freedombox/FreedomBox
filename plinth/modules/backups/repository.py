# SPDX-License-Identifier: AGPL-3.0-or-later
"""Remote and local Borg backup repositories."""

import abc
import contextlib
import io
import logging
import os
import re
import subprocess
from uuid import uuid1

from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy

from . import (_backup_handler, api, errors, get_known_hosts_path, privileged,
               restore_archive_handler, split_path, store)
from .schedule import Schedule

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
        'message': _('Repository not found'),
        'raise_as': errors.BorgRepositoryDoesNotExistError,
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
    flags: dict[str, bool] = {}
    is_mounted = True
    known_credentials: list[str] = []

    def __init__(self, path, credentials=None, uuid=None, schedule=None,
                 **kwargs):
        """Instantiate a new repository."""
        self._path = path
        self.credentials = credentials or {}
        self.uuid = uuid or str(uuid1())
        self.kwargs = kwargs
        schedule = schedule or {}
        schedule['repository_uuid'] = self.uuid
        self.schedule = Schedule(**schedule)

    @classmethod
    def load(cls, uuid):
        """Create instance by loading from database."""
        storage = dict(store.get(uuid))
        path = storage.pop('path')
        storage.pop('uuid')
        credentials = storage.setdefault('credentials', {})
        storage.pop('credentials')
        schedule = storage.setdefault('schedule', {})
        storage.pop('schedule')

        return cls(path, credentials, uuid, schedule, **storage)

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
    def prepare():
        """Prepare the repository for operations."""

    @staticmethod
    def cleanup():
        """Cleanup the repository after operations."""

    def get_info(self):
        """Return Borg information about a repository."""
        with self._handle_errors():
            output = privileged.info(self.borg_path,
                                     self._get_encryption_passpharse())

        if output['encryption']['mode'] == 'none' and \
           self._get_encryption_data():
            raise errors.BorgUnencryptedRepository(
                _('Existing repository is not encrypted.'))

        return output

    def get_view_content(self):
        """Get archives with additional information as needed by the view."""
        repository = {
            'uuid': self.uuid,
            'name': self.name,
            'storage_type': self.storage_type,
            'is_encrypted': bool(self._get_encryption_data()),
            'flags': self.flags,
            'error': None,
        }
        try:
            repository['mounted'] = self.is_mounted
            if repository['mounted']:
                repository['archives'] = self.list_archives()
        except (errors.BorgError, Exception) as err:
            repository['error'] = str(err)

        return repository

    def remove(self):
        """Remove a borg repository"""

    def list_archives(self):
        """Return list of archives in this repository."""
        with self._handle_errors():
            archives = privileged.list_repo(
                self.borg_path, self._get_encryption_passpharse())['archives']
        return sorted(archives, key=lambda archive: archive['start'],
                      reverse=True)

    def create_archive(self, archive_name, app_ids, archive_comment=None):
        """Create a new archive in this repository with given name."""
        archive_path = self._get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.backup_apps(_backup_handler, path=archive_path, app_ids=app_ids,
                        encryption_passphrase=passphrase,
                        archive_comment=archive_comment)

    def delete_archive(self, archive_name):
        """Delete an archive with given name from this repository."""
        archive_path = self._get_archive_path(archive_name)
        with self._handle_errors():
            privileged.delete_archive(archive_path,
                                      self._get_encryption_passpharse())

    def initialize(self):
        """Initialize / create a borg repository."""
        encryption = 'none'
        if 'encryption_passphrase' in self.credentials and \
           self.credentials['encryption_passphrase']:
            encryption = 'repokey'

        try:
            with self._handle_errors():
                privileged.init(self.borg_path, encryption,
                                self._get_encryption_passpharse())
        except errors.BorgRepositoryExists:
            pass

        self.get_info()  # If password is incorrect raise an error early.

    def _get_encryption_data(self):
        """Return additional dictionary data to send to backups call."""
        passphrase = self.credentials.get('encryption_passphrase', None)
        if passphrase:
            return {'encryption_passphrase': passphrase}

        return {}

    @contextlib.contextmanager
    def _handle_errors(self):
        """Parse exceptions into more specific ones."""
        try:
            yield
        except Exception as exception:
            self.reraise_known_error(exception)

    def _get_encryption_passpharse(self):
        """Return encryption passphrase or raise an exception."""
        for key in self.credentials.keys():
            if key not in self.known_credentials:
                raise ValueError('Unknown credentials entry: %s' % key)

        return self.credentials.get('encryption_passphrase', None)

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

        with self._handle_errors():
            proc, read_fd, input_ = privileged.export_tar(
                self._get_archive_path(archive_name),
                self._get_encryption_passpharse(), _raw_output=True)

        os.close(read_fd)  # Don't use the pipe for communication, just stdout
        proc.stdin.write(input_)
        proc.stdin.close()
        proc.stderr.close()  # writing to stderr in child will cause SIGPIPE

        return BufferedReader(proc.stdout)

    def _get_archive_path(self, archive_name):
        """Return full borg path for an archive."""
        return '::'.join([self.borg_path, archive_name])

    @staticmethod
    def reraise_known_error(err):
        """Look whether the caught error is known and reraise it accordingly"""
        stdout = getattr(err, 'stdout', b'').decode()
        stderr = getattr(err, 'stderr', b'').decode()
        caught_error = str((err, err.args, stdout, stderr))
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
        with self._handle_errors():
            return privileged.get_archive_apps(
                archive_path, self._get_encryption_passpharse())

    def restore_archive(self, archive_name, app_ids=None):
        """Restore an archive from this repository to the system."""
        archive_path = self._get_archive_path(archive_name)
        passphrase = self.credentials.get('encryption_passphrase', None)
        api.restore_apps(restore_archive_handler, app_ids=app_ids,
                         create_subvolume=False, backup_file=archive_path,
                         encryption_passphrase=passphrase)

    def _get_storage_format(self):
        """Return a dict representing the repository."""
        storage = {
            'path': self._path,
            'storage_type': self.storage_type,
            'added_by_module': 'backups',
            'credentials': self.credentials,
            'schedule': self.schedule.get_storage_format()
        }
        if self.uuid:
            storage['uuid'] = self.uuid

        return storage

    def save(self):
        """Save the repository in store (kvstore)."""
        storage = self._get_storage_format()
        self.uuid = store.update_or_add(storage)


class RootBorgRepository(BaseBorgRepository):
    """Borg repository on the root filesystem."""
    UUID = 'root'
    PATH = '/var/lib/freedombox/borgbackup'

    storage_type = 'root'
    name = format_lazy(_('{box_name} storage'), box_name=_(cfg.box_name))
    borg_path = PATH
    sort_order = 10
    is_mounted = True

    def __init__(self, path=None, credentials=None, uuid=None, schedule=None,
                 **kwargs):
        """Initialize the repository object."""
        super().__init__(self.PATH, credentials, self.UUID, schedule, **kwargs)


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

    def __init__(self, path, credentials=None, uuid=None, schedule=None,
                 verified=None, **kwargs):
        """Instantiate a new repository."""
        super().__init__(path, credentials, uuid, schedule, **kwargs)
        self.verified = verified or False

    def _get_storage_format(self):
        """Return a dict representing the repository."""
        storage = super()._get_storage_format()
        storage['verified'] = self.verified
        return storage

    def is_usable(self):
        """Return whether repository is usable."""
        return self.verified

    @property
    def borg_path(self):
        """Return the path to use for backups actions.

        This is the mount point for the remote SSH repositories.

        """
        return self._mountpoint

    def prepare(self):
        """Prepare the repository for operations by mounting."""
        if not self.is_usable():
            raise errors.SshfsError('Remote host not verified')

        self._umount_ignore_errors()  # In case the connection is stale.
        self.mount()

    def cleanup(self):
        """Cleanup the repository after operations by unmounting."""
        self._umount_ignore_errors()

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
        with self._handle_errors():
            return privileged.is_mounted(self._mountpoint)

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
        kwargs = {'user_known_hosts_file': str(known_hosts_path)}
        if 'ssh_password' in self.credentials and self.credentials[
                'ssh_password']:
            kwargs['password'] = self.credentials['ssh_password']

        if 'ssh_keyfile' in self.credentials and self.credentials[
                'ssh_keyfile']:
            kwargs['ssh_keyfile'] = self.credentials['ssh_keyfile']

        with self._handle_errors():
            privileged.mount(self._mountpoint, self._path, **kwargs)

    def umount(self):
        """Unmount the remote path that was mounted locally using sshfs."""
        if not self.is_mounted:
            return

        with self._handle_errors():
            privileged.umount(self._mountpoint)

    def _umount_ignore_errors(self):
        """Run unmount operation and ignore any exceptions thrown."""
        try:
            self.umount()
        except Exception as exception:
            logger.warning('Unable to unmount repository', exc_info=exception)

    def remove(self):
        """Remove a repository from the kvstore and delete its mountpoint."""
        self.umount()
        store.delete(self.uuid)
        try:
            if os.path.exists(self._mountpoint):
                try:
                    self.umount()
                except Exception:
                    pass
                if not os.listdir(self._mountpoint):
                    os.rmdir(self._mountpoint)
        except Exception as err:
            logger.error(err)

    def _ensure_remote_directory(self):
        """Create remote SSH directory if it does not exist."""
        username, hostname, dir_path = split_path(self.path)
        if dir_path == '':
            dir_path = '.'

        if dir_path[0] == '~':
            dir_path = '.' + dir_path[1:]

        password = self.credentials['ssh_password']

        # Ensure remote directory exists, check contents
        env = {'SSHPASS': password}
        known_hosts_path = str(get_known_hosts_path())
        subprocess.run([
            'sshpass', '-e', 'ssh', '-o',
            f'UserKnownHostsFile={known_hosts_path}', f'{username}@{hostname}',
            'mkdir', '-p', dir_path
        ], check=True, env=env)


def get_repositories():
    """Get all repositories of a given storage type."""
    repositories = []
    storages = store.get_storages()
    for uuid in storages:
        repositories.append(get_instance(uuid))

    if RootBorgRepository.UUID not in storages:
        repositories.append(get_instance(RootBorgRepository.UUID))

    return sorted(repositories, key=lambda x: x.sort_order)


def get_instance(uuid):
    """Create a local or SSH repository object instance."""
    if uuid == RootBorgRepository.UUID:
        try:
            return RootBorgRepository.load(uuid)
        except KeyError:
            return RootBorgRepository()

    storage = store.get(uuid)
    if storage['storage_type'] == 'ssh':
        return SshBorgRepository.load(uuid)

    return BorgRepository.load(uuid)
