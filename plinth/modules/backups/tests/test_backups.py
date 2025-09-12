# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test the backups action script.
"""

import os
import pathlib
import subprocess
import uuid

import pytest

from plinth.modules import backups
from plinth.modules.backups import privileged
from plinth.modules.backups.repository import BorgRepository, SshBorgRepository
from plinth.tests import config as test_config

pytestmark = pytest.mark.usefixtures('needs_root', 'needs_borg', 'load_cfg',
                                     'mock_privileged')

privileged_modules_to_mock = ['plinth.modules.backups.privileged']

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
    path = backup_directory / 'borgbackup'
    repository = BorgRepository(str(path))
    repository.initialize()
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
    archive_comment = 'test_archive_comment'
    path = backup_directory / repo_name

    repository = BorgRepository(str(path))
    repository.initialize()
    archive_path = "::".join([str(path), archive_name])
    privileged.create_archive(archive_path, [str(data_directory)],
                              archive_comment)

    archive = repository.list_archives()[0]
    assert archive['name'] == archive_name
    assert archive['comment'] == archive_comment

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
    path = os.path.join(test_config.backups_ssh_path, str(uuid.uuid1()))
    privileged.init(path, 'repokey', **_get_borg_arguments(credentials))

    info = privileged.info(path, **_get_borg_arguments(credentials))
    assert info['encryption']['mode'] == 'repokey'


def _get_borg_arguments(credentials):
    """Get credential arguments for running borg privileged actions."""
    return {
        'passphrase': credentials.get('encryption_passphrase', None),
        'ssh_keyfile': credentials.get('ssh_keyfile')
    }


@pytest.mark.usefixtures('needs_ssh_config')
def test_sshfs_mount_password():
    """Test (un)mounting if password for a remote location is given"""
    credentials = _get_credentials()
    ssh_path = test_config.backups_ssh_path

    repository = SshBorgRepository(ssh_path, credentials)
    repository.mount()
    assert repository.is_mounted
    repository.umount()
    assert not repository.is_mounted


@pytest.mark.usefixtures('needs_ssh_config')
def test_sshfs_mount_keyfile():
    """Test (un)mounting if keyfile for a remote location is given"""
    credentials = _get_credentials()
    ssh_path = test_config.backups_ssh_path

    repository = SshBorgRepository(ssh_path, credentials)
    repository.mount()
    assert repository.is_mounted
    repository.umount()
    assert not repository.is_mounted


def test_access_nonexisting_url():
    """Test accessing a non-existent URL."""
    repo_url = "user@%s.com.au:~/repo" % str(uuid.uuid1())
    repository = SshBorgRepository(repo_url, _dummy_credentials)
    with pytest.raises(backups.errors.BorgRepositoryDoesNotExistError):
        repository.get_info()


def test_inaccessible_repo_url():
    """Test accessing an existing URL with wrong credentials."""
    repo_url = 'user@heise.de:~/repo'
    repository = SshBorgRepository(repo_url, _dummy_credentials)
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
