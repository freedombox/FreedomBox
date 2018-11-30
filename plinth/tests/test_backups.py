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

import os
import shutil
import tempfile
import unittest

from plinth import cfg
from plinth.modules import backups
from plinth.modules.backups.repository import BorgRepository, SshBorgRepository
from plinth import actions

from . import config

euid = os.geteuid()


class TestBackups(unittest.TestCase):
    """Test creating, reading and deleting a repository"""

    @classmethod
    def setUpClass(cls):
        """Initial setup for all the classes."""
        cls.action_directory = tempfile.TemporaryDirectory()
        cls.backup_directory = tempfile.TemporaryDirectory()
        cls.data_directory = os.path.join(os.path.dirname(
            os.path.realpath(__file__)), 'data')
        cfg.actions_dir = cls.action_directory.name
        actions_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                                   'actions')
        shutil.copy(os.path.join(actions_dir, 'backups'), cfg.actions_dir)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all the tests are completed."""
        cls.action_directory.cleanup()
        cls.backup_directory.cleanup()

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_nonexisting_repository(self):
        nonexisting_dir = os.path.join(self.backup_directory.name,
                                       'does_not_exist')
        repository = BorgRepository(nonexisting_dir)
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            repository.get_info()

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_empty_dir(self):
        empty_dir = os.path.join(self.backup_directory.name, 'empty_dir')
        os.mkdir(empty_dir)
        repository = BorgRepository(empty_dir)
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            repository.get_info()

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_create_unencrypted_repository(self):
        repo_path = os.path.join(self.backup_directory.name, 'borgbackup')
        repository = BorgRepository(repo_path)
        repository.create_repository()
        info = repository.get_info()
        assert 'encryption' in info

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_create_and_delete_archive(self):
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
        actions.superuser_run(
            'backups', ['create-archive', '--path', archive_path, '--paths',
                        self.data_directory])

        archive = repository.list_archives()[0]
        assert archive['name'] == archive_name

        repository.delete_archive(archive_name)
        content = repository.list_archives()
        assert len(content) == 0

    @unittest.skipUnless(euid == 0 and config.backups_ssh_path,
                         'Needs to be root and ssh credentials provided')
    def test_ssh_mount(self):
        """Test (un)mounting if credentials for a remote location are given"""
        credentials = self.get_credentials()
        if not credentials:
            return
        ssh_path = config.backups_ssh_path

        ssh_repo = SshBorgRepository(uuid='plinth_test_sshfs',
                                     path=ssh_path,
                                     credentials=credentials)
        ssh_repo.mount()
        assert ssh_repo.is_mounted
        ssh_repo.umount()
        assert not ssh_repo.is_mounted

    @unittest.skipUnless(euid == 0 and config.backups_ssh_path,
                         'Needs to be root and ssh credentials provided')
    def test_ssh_create_encrypted_repository(self):
        credentials = self.get_credentials()
        encrypted_repo = os.path.join(self.backup_directory.name,
                                      'borgbackup_encrypted')
        credentials['encryption_passphrase'] = '12345'
        repository = SshBorgRepository(path=encrypted_repo,
                                       credentials=credentials)
        # 'borg init' creates missing folders automatically
        repository.create_repository(encryption='repokey')
        assert repository.get_info()

    def get_credentials(self):
        """
        Get access params for a remote location.
        Return an empty dict if no valid access params are found.
        """
        credentials = {}
        if config.backups_ssh_password:
            credentials['ssh_password'] = config.backups_ssh_password
        elif config.backups_ssh_keyfile:
            credentials['ssh_keyfile'] = config.backups_ssh_keyfile
        return credentials
