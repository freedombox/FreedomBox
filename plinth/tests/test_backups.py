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
from plinth.modules.backups import sshfs
from plinth import actions

from . import config

try:
    from . import config_local as config
except ImportError:
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
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            backups.test_connection(nonexisting_dir)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_empty_dir(self):
        empty_dir = os.path.join(self.backup_directory.name, 'empty_dir')
        os.mkdir(empty_dir)
        with self.assertRaises(backups.errors.BorgRepositoryDoesNotExistError):
            backups.test_connection(empty_dir)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_create_unencrypted_repository(self):
        repo_path = os.path.join(self.backup_directory.name, 'borgbackup')
        backups.create_repository(repo_path, 'none')
        info = backups.get_info(repo_path)
        assert 'encryption' in info

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_create_encrypted_repository(self):
        repo_path = os.path.join(self.backup_directory.name,
                                 'borgbackup_encrypted')
        # 'borg init' creates missing folders automatically
        access_params = {'encryption_passphrase': '12345'}
        backups.create_repository(repo_path, 'repokey',
                                  access_params=access_params)
        assert backups.get_info(repo_path, access_params)
        assert backups.test_connection(repo_path, access_params)

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

        backups.create_repository(repo_path, 'none')
        archive_path = "::".join([repo_path, archive_name])
        actions.superuser_run(
            'backups', ['create-archive', '--path', archive_path, '--paths',
                        self.data_directory])

        archive = backups.list_archives(repo_path)[0]
        assert archive['name'] == archive_name

        backups.delete_archive(archive_path)
        content = backups.list_archives(repo_path)
        assert len(content) == 0

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_is_mounted(self):
        assert not sshfs.is_mounted(self.action_directory.name)
        assert sshfs.is_mounted('/')

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_mount(self):
        """Test (un)mounting if credentials for a remote location are given"""
        import ipdb; ipdb.set_trace()
        if config.backups_ssh_path:
            access_params = self.get_remote_access_params()
            if not access_params:
                return
            mountpoint = config.backups_ssh_mountpoint
            ssh_path = config.backups_ssh_path

            sshfs.mount(ssh_path, mountpoint, access_params)
            assert sshfs.is_mounted(mountpoint)
            sshfs.umount(mountpoint)
            assert not sshfs.is_mounted(mountpoint)

    def get_remote_access_params(self):
        """
        Get access params for a remote location.
        Return an empty dict if no valid access params are found.
        """
        access_params = {}
        if config.backups_ssh_password:
            access_params['ssh_password'] = config.backups_ssh_password
        elif config.backups_ssh_keyfile:
            access_params['ssh_keyfile'] = config.backups_ssh_keyfile
        return access_params
