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
import os
import logging

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.errors import ActionError

from . import api, network_storage, _backup_handler, ROOT_REPOSITORY_NAME
from .errors import BorgError, BorgRepositoryDoesNotExistError

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
    }]


class BorgRepository(object):
    """Borg repository on the root filesystem"""
    command = 'backups'
    storage_type = 'root'
    name = ROOT_REPOSITORY_NAME
    is_mounted = True

    def __init__(self, path, credentials={}):
        self.path = path
        self.credentials = credentials

    def get_info(self):
        output = self._run(['info', '--path', self.path])
        return json.loads(output)

    def list_archives(self):
        output = self._run(['list-repo', '--path', self.path])
        return json.loads(output)['archives']

    def get_view_content(self):
        """Get archives with additional information as needed by the view"""
        repository = {
            'name': self.name,
            'type': self.storage_type,
            'error': ''
        }
        try:
            repository['archives'] = self.list_archives()
            repository['mounted'] = self.is_mounted
            error = ''
        except (BorgError, ActionError) as err:
            error = str(err)
        repository['error'] = error
        return repository

    def delete_archive(self, archive_name):
        archive_path = self.get_archive_path(archive_name)
        self._run(['delete-archive', '--path', archive_path])

    def remove(self):
        """Remove a borg repository"""
        raise NotImplementedError

    def create_archive(self, app_names, archive_name):
        api.backup_apps(_backup_handler, app_names=app_names,
                        label=archive_name),

    def create_repository(self):
        self._run(['init', '--path', self.path, '--encryption', 'none'])

    def download_archive(self, name):
        # TODO
        pass

    def get_archive(self, name):
        # TODO: can't we get this archive directly?
        for archive in self.list_archives():
            if archive['name'] == name:
                return archive

        return None

    def get_archive_apps(self, archive_name):
        """Get list of apps included in an archive."""
        archive_path = self.get_archive_path(archive_name)
        output = self._run(['get-archive-apps', '--path', archive_path])
        return output.splitlines()

    def restore_archive(self):
        # TODO
        pass

    def get_archive_path(self, archive_name):
        return "::".join([self.path, archive_name])

    def _get_arguments(self, arguments, credentials):
        kwargs = {}
        if 'encryption_passphrase' in credentials and \
           credentials['encryption_passphrase']:
            arguments += ['--encryption-passphrase',
                          credentials['encryption_passphrase']]
        return (arguments, kwargs)

    def _run(self, arguments, superuser=True):
        """Run a backups action script command.

        Automatically passes on credentials via self._get_arguments to the
        backup script via environment variables or input, except if you
        set use_credentials to False.
        """
        try:
            if superuser:
                return actions.superuser_run(self.command, arguments)
            else:
                return actions.run(self.command, arguments)
        except ActionError as err:
            self.reraise_known_error(err)

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

    def __init__(self, uuid=None, path=None, credentials=None, **kwargs):
        """
        Provide a uuid to instanciate an existing repository,
        or 'path' and 'credentials' for a new repository.
        """
        if uuid:
            self.uuid = uuid
            # If all data are given, instanciate right away.
            if path and credentials:
                self.path = path
                self.credentials = credentials
            else:
                self._load_from_kvstore()
        # No uuid given: new instance.
        elif path and credentials:
            self.path = path
            self.credentials = credentials
        else:
            raise ValueError('Invalid arguments.')

    @property
    def mountpoint(self):
        return os.path.join(SSHFS_MOUNTPOINT, self.uuid)

    @property
    def name(self):
        return self.path

    @property
    def is_mounted(self):
        output = self._run(['is-mounted', '--mountpoint', self.mountpoint])
        return json.loads(output)

    def _load_from_kvstore(self):
        storage = network_storage.get(self.uuid)
        try:
            self.credentials = storage['credentials']
        except KeyError:
            self.credentials = {}
        self.path = storage['path']

    def _get_network_storage_format(self, store_credentials):
        storage = {
            'path': self.path,
            'storage_type': self.storage_type,
            'added_by_module': 'backups'
        }
        if hasattr(self, 'uuid'):
            storage['uuid'] = self.uuid
        if store_credentials:
            storage['credentials'] = self.credentials
        return storage

    def create_archive(self, app_names, archive_name):
        raise NotImplementedError
        # api.backup_apps(_backup_handler, app_names=app_names,

    def create_repository(self, encryption):
        if encryption not in SUPPORTED_BORG_ENCRYPTION:
            raise ValueError('Unsupported encryption: %s' % encryption)
        self._run(['init', '--path', self.path, '--encryption', encryption])

    def save(self, store_credentials=True):
        storage = self._get_network_storage_format(store_credentials)
        self.uuid = network_storage.update_or_add(storage)

    def mount(self):
        cmd = ['mount', '--mountpoint', self.mountpoint, '--path', self.path]
        self._run(cmd)

    def umount(self):
        self._run(['umount', '--mountpoint', self.mountpoint])

    def remove(self):
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

    def _get_arguments(self, arguments, credentials):
        arguments, kwargs = super()._get_arguments(arguments, credentials)
        if 'ssh_password' in credentials and credentials['ssh_password']:
            kwargs['input'] = credentials['ssh_password'].encode()
        if 'ssh_keyfile' in credentials and credentials['ssh_keyfile']:
            arguments += ['--ssh-keyfile', credentials['ssh_keyfile']]
        return (arguments, kwargs)

    def _run(self, arguments, superuser=True, use_credentials=True):
        """Run a backups action script command.

        Automatically passes on credentials via self._get_arguments to the
        backup script via environment variables or input, except if you
        set use_credentials to False.
        """
        kwargs = {}
        if use_credentials:
            if not self.credentials:
                msg = 'Cannot access ssh repo without credentials'
                raise BorgError(msg)
            for key in self.credentials.keys():
                if key not in self.KNOWN_CREDENTIALS:
                    raise ValueError('Unknown credentials entry: %s' % key)
            arguments, kwargs = self._get_arguments(arguments,
                                                    self.credentials)
        try:
            if superuser:
                return actions.superuser_run(self.command, arguments, **kwargs)
            else:
                return actions.run(self.command, arguments, **kwargs)
        except ActionError as err:
            self.reraise_known_error(err)


def get_ssh_repositories():
    """Get all SSH Repositories including the archive content"""
    repositories = {}
    for storage in network_storage.get_storages():
        repository = SshBorgRepository(**storage)
        repositories[storage['uuid']] = repository.get_view_content()
    return repositories
