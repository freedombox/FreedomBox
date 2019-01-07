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
Test the backups action script.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
import uuid

from plinth import cfg
from plinth.modules import backups
from plinth.modules.backups.repository import BorgRepository, SshBorgRepository
from plinth import actions

from plinth.tests import config as test_config

euid = os.geteuid()


def _borg_is_installed():
    """Return whether borg is installed on the system."""
    try:
        subprocess.run(['borg', '--version'], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
        return True
    except FileNotFoundError:
        return False


class TestBackups(unittest.TestCase):
    """Test creating, reading and deleting a repository"""
    # try to access a non-existing url and a URL that exists but does not
    # grant access
    nonexisting_repo_url = "user@%s.com.au:~/repo" % str(uuid.uuid1())
    inaccessible_repo_url = "user@heise.de:~/repo"
    dummy_credentials = {'ssh_password': 'invalid_password'}
    repokey_encryption_passphrase = '12345'

    @classmethod
    def setUpClass(cls):
        """Initial setup for all the classes."""
        cls.action_directory = tempfile.TemporaryDirectory()
        cls.backup_directory = tempfile.TemporaryDirectory()
        cls.data_directory = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'backup_data')
        cls.actions_dir_factory = cfg.actions_dir
        cfg.actions_dir = cls.action_directory.name
        actions_dir = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..', 'actions')
        shutil.copy(os.path.join(actions_dir, 'backups'), cfg.actions_dir)
        shutil.copy(os.path.join(actions_dir, 'sshfs'), cfg.actions_dir)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all the tests are completed."""
        cls.action_directory.cleanup()
        cls.backup_directory.cleanup()
        cfg.actions_dir = cls.actions_dir_factory

    @unittest.skipUnless(euid == 0 and _borg_is_installed(),
                         'Needs to be root')
    def test_nonexisting_repository(self):
        nonexisting_dir = os.path.join(self.backup_directory.name,
                                       'does_not_exist')
        repository = BorgRepository(nonexisting_dir)
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            repository.get_info()

    @unittest.skipUnless(euid == 0 and _borg_is_installed(),
                         'Needs to be root')
    def test_empty_dir(self):
        empty_dir = os.path.join(self.backup_directory.name, 'empty_dir')
        os.mkdir(empty_dir)
        repository = BorgRepository(empty_dir)
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            repository.get_info()

    @unittest.skipUnless(euid == 0 and _borg_is_installed(),
                         'Needs to be root')
    def test_create_unencrypted_repository(self):
        repo_path = os.path.join(self.backup_directory.name, 'borgbackup')
        repository = BorgRepository(repo_path)
        repository.create_repository()
        info = repository.get_info()
        self.assertTrue('encryption' in info)

    @unittest.skipUnless(euid == 0 and _borg_is_installed(),
                         'Needs to be root')
    def test_create_export_delete_archive(self):
        """
        - Create a repo
        - Create an archive
        - Verify archive content
        - Delete archive
        """
        repo_name = 'test_create_and_delete'
        archive_name = 'first_archive'
        repo_path = os.path.join(self.backup_directory.name, repo_name)

        repository = BorgRepository(repo_path)
        repository.create_repository()
        archive_path = "::".join([repo_path, archive_name])
        actions.superuser_run('backups', [
            'create-archive', '--path', archive_path, '--paths',
            self.data_directory
        ])

        archive = repository.list_archives()[0]
        self.assertEquals(archive['name'], archive_name)

        repository.delete_archive(archive_name)
        content = repository.list_archives()
        self.assertEquals(len(content), 0)

    @unittest.skipUnless(euid == 0 and _borg_is_installed()
                         and test_config.backups_ssh_path,
                         'Needs to be root and ssh password provided')
    def test_remote_backup_actions(self):
        """
        Test creating an encrypted remote repository using borg directly.

        This relies on borgbackups being installed on the remote machine.
        """
        credentials = self.get_credentials(add_encryption_passphrase=True)
        repo_path = os.path.join(test_config.backups_ssh_path,
                                 str(uuid.uuid1()))
        arguments = ['init', '--path', repo_path, '--encryption', 'repokey']
        arguments, kwargs = self.append_borg_arguments(arguments, credentials)
        actions.superuser_run('backups', arguments, **kwargs)

        arguments = ['info', '--path', repo_path]
        arguments, kwargs = self.append_borg_arguments(arguments, credentials)
        info = actions.superuser_run('backups', arguments, **kwargs)
        info = json.loads(info)
        self.assertEquals(info['encryption']['mode'], 'repokey')

    def append_borg_arguments(self, arguments, credentials):
        """Append run arguments for running borg directly"""
        kwargs = {}
        passphrase = credentials.get('encryption_passphrase', None)
        if passphrase:
            arguments += ['--encryption-passphrase', passphrase]
        if 'ssh_password' in credentials and credentials['ssh_password']:
            kwargs['input'] = credentials['ssh_password'].encode()
        if 'ssh_keyfile' in credentials and credentials['ssh_keyfile']:
            arguments += ['--ssh-keyfile', credentials['ssh_keyfile']]
        return (arguments, kwargs)

    @unittest.skipUnless(euid == 0 and _borg_is_installed()
                         and test_config.backups_ssh_path,
                         'Needs to be root and ssh password provided')
    def test_sshfs_mount_password(self):
        """Test (un)mounting if password for a remote location is given"""
        credentials = self.get_credentials()
        ssh_path = test_config.backups_ssh_path

        repository = SshBorgRepository(path=ssh_path, credentials=credentials,
                                       automount=False)
        repository.mount()
        self.assertTrue(repository.is_mounted)
        repository.umount()
        self.assertFalse(repository.is_mounted)

    @unittest.skipUnless(euid == 0 and _borg_is_installed()
                         and test_config.backups_ssh_keyfile,
                         'Needs to be root and ssh keyfile provided')
    def test_sshfs_mount_keyfile(self):
        """Test (un)mounting if keyfile for a remote location is given"""
        credentials = self.get_credentials()
        ssh_path = test_config.backups_ssh_path

        repository = SshBorgRepository(path=ssh_path, credentials=credentials,
                                       automount=False)
        repository.mount()
        self.assertTrue(repository.is_mounted)
        repository.umount()
        self.assertFalse(repository.is_mounted)

    @unittest.skipUnless(euid == 0 and _borg_is_installed(),
                         'Needs to be root')
    def test_access_nonexisting_url(self):
        repository = SshBorgRepository(path=self.nonexisting_repo_url,
                                       credentials=self.dummy_credentials,
                                       automount=False)
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            repository.get_info()

    @unittest.skipUnless(euid == 0 and _borg_is_installed(),
                         'Needs to be root')
    def test_inaccessible_repo_url(self):
        """Test accessing an existing URL with wrong credentials"""
        repository = SshBorgRepository(path=self.inaccessible_repo_url,
                                       credentials=self.dummy_credentials,
                                       automount=False)
        with self.assertRaises(backups.errors.BorgError):
            repository.get_info()

    def get_credentials(self, add_encryption_passphrase=False):
        """
        Get access params for a remote location.
        Return an empty dict if no valid access params are found.
        """
        credentials = {}
        if test_config.backups_ssh_password:
            credentials['ssh_password'] = test_config.backups_ssh_password
        elif test_config.backups_ssh_keyfile:
            credentials['ssh_keyfile'] = test_config.backups_ssh_keyfile
        if add_encryption_passphrase:
            credentials['encryption_passphrase'] = \
                self.repokey_encryption_passphrase

        return credentials
