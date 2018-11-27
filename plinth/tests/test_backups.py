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

euid = os.geteuid()


class TestBackups(unittest.TestCase):
    """Test creating, reading and deleting a repository"""

    @classmethod
    def setUpClass(cls):
        """Initial setup for all the classes."""
        cls.action_directory = tempfile.TemporaryDirectory()
        cls.backup_directory = tempfile.TemporaryDirectory()
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
        passphrase = '12345'
        # create_repository is supposed to create the folder automatically
        # if it does not exist
        backups.create_repository(repo_path, 'repokey',
                                  encryption_passphrase=passphrase)
        assert backups.get_info(repo_path, encryption_passphrase=passphrase)
        assert backups.test_connection(repo_path,
                                       encryption_passphrase=passphrase)
