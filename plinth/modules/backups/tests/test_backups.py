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
import pathlib
import subprocess
import uuid

import pytest

from plinth.modules import backups
from plinth.modules.backups.repository import BorgRepository, SshBorgRepository
from plinth import actions

from plinth.tests import config as test_config

pytestmark = pytest.mark.usefixtures('needs_root', 'needs_borg', 'load_cfg')

# try to access a non-existing url and a URL that exists but does not
# grant access
_dummy_credentials = {'ssh_password': 'invalid_password'}
_repokey_encryption_passphrase = '12345'


@pytest.fixture(name='needs_borg')
def fixture_needs_borg():
    """Return whether borg is installed on the system."""
    try:
        subprocess.run(['borg', '--version'], stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL, check=True)
    except FileNotFoundError:
        pytest.skip('Needs borg installed')


@pytest.fixture(name='needs_ssh_config')
def fixture_needs_ssh_config():
    """Skip test if SSH details is not available in test configuration."""
    if not test_config.backups_ssh_path:
        pytest.skip('Needs SSH password provided')


@pytest.fixture(name='data_directory')
def fixture_data_directory():
    """Return directory where backup data is stored."""
    return pathlib.Path(__file__).parent / 'backup_data'


@pytest.fixture(name='backup_directory')
def fixture_backup_directory(tmp_path):
    """Create and cleanup a backup directory."""
    return tmp_path


def test_nonexisting_repository(backup_directory):
    """Test that non-existent directory as borg repository throws error."""
    nonexisting_dir = backup_directory / 'does_not_exist'
    repository = BorgRepository(str(nonexisting_dir))
    with pytest.raises(backups.errors.BorgRepositoryDoesNotExistError):
        repository.get_info()


def test_empty_dir(backup_directory):
    """Test that empty directory as borg repository throws error."""
    empty_dir = backup_directory / 'empty_dir'
    empty_dir.mkdir()
    repository = BorgRepository(str(empty_dir))
    with pytest.raises(backups.errors.BorgRepositoryDoesNotExistError):
        repository.get_info()


def test_create_unencrypted_repository(backup_directory):
    """Test creating an unencrypted repository."""
    repo_path = backup_directory / 'borgbackup'
    repository = BorgRepository(str(repo_path))
    repository.create_repository()
    info = repository.get_info()
    assert 'encryption' in info


def test_create_export_delete_archive(data_directory, backup_directory):
    """
    - Create a repo
    - Create an archive
    - Verify archive content
    - Delete archive
    """
    repo_name = 'test_create_and_delete'
    archive_name = 'first_archive'
    repo_path = backup_directory / repo_name

    repository = BorgRepository(str(repo_path))
    repository.create_repository()
    archive_path = "::".join([str(repo_path), archive_name])
    actions.superuser_run('backups', [
        'create-archive', '--path', archive_path, '--paths',
        str(data_directory)
    ])

    archive = repository.list_archives()[0]
    assert archive['name'] == archive_name

    repository.delete_archive(archive_name)
    content = repository.list_archives()
    assert not content


@pytest.mark.usefixtures('needs_ssh_config')
def test_remote_backup_actions():
    """
    Test creating an encrypted remote repository using borg directly.

    This relies on borgbackups being installed on the remote machine.
    """
    credentials = _get_credentials(add_encryption_passphrase=True)
    repo_path = os.path.join(test_config.backups_ssh_path, str(uuid.uuid1()))
    arguments = ['init', '--path', repo_path, '--encryption', 'repokey']
    arguments, kwargs = _append_borg_arguments(arguments, credentials)
    actions.superuser_run('backups', arguments, **kwargs)

    arguments = ['info', '--path', repo_path]
    arguments, kwargs = _append_borg_arguments(arguments, credentials)
    info = actions.superuser_run('backups', arguments, **kwargs)
    info = json.loads(info)
    assert info['encryption']['mode'] == 'repokey'


def _append_borg_arguments(arguments, credentials):
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


@pytest.mark.usefixtures('needs_ssh_config')
def test_sshfs_mount_password():
    """Test (un)mounting if password for a remote location is given"""
    credentials = _get_credentials()
    ssh_path = test_config.backups_ssh_path

    repository = SshBorgRepository(path=ssh_path, credentials=credentials,
                                   automount=False)
    repository.mount()
    assert repository.is_mounted
    repository.umount()
    assert not repository.is_mounted


@pytest.mark.usefixtures('needs_ssh_config')
def test_sshfs_mount_keyfile():
    """Test (un)mounting if keyfile for a remote location is given"""
    credentials = _get_credentials()
    ssh_path = test_config.backups_ssh_path

    repository = SshBorgRepository(path=ssh_path, credentials=credentials,
                                   automount=False)
    repository.mount()
    assert repository.is_mounted
    repository.umount()
    assert not repository.is_mounted


def test_access_nonexisting_url():
    """Test accessing a non-existent URL."""
    repo_url = "user@%s.com.au:~/repo" % str(uuid.uuid1())
    repository = SshBorgRepository(
        path=repo_url, credentials=_dummy_credentials, automount=False)
    with pytest.raises(backups.errors.BorgRepositoryDoesNotExistError):
        repository.get_info()


def test_inaccessible_repo_url():
    """Test accessing an existing URL with wrong credentials."""
    repo_url = 'user@heise.de:~/repo'
    repository = SshBorgRepository(
        path=repo_url, credentials=_dummy_credentials, automount=False)
    with pytest.raises(backups.errors.BorgError):
        repository.get_info()


def _get_credentials(add_encryption_passphrase=False):
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
            _repokey_encryption_passphrase

    return credentials
