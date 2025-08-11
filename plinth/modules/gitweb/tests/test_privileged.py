# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test module for gitweb module operations."""

import pathlib

import pytest
from django.forms import ValidationError

from plinth.modules.gitweb import privileged

REPO_NAME = 'Test-repo'
REPO_DATA = {
    'name': REPO_NAME,
    'description': '',
    'owner': '',
    'access': 'private',
}

pytestmark = pytest.mark.usefixtures('mock_privileged')
privileged_modules_to_mock = ['plinth.modules.gitweb.privileged']
git_installed = pytest.mark.skipif(not pathlib.Path('/usr/bin/git').exists(),
                                   reason='git is not installed')


@pytest.fixture(autouse=True)
def fixture_set_repo_path(tmpdir):
    """Set a repository path in the actions module."""
    privileged.GIT_REPO_PATH = tmpdir


@pytest.fixture(name='existing_repo')
def fixture_existing_repo():
    """A fixture to create a repository."""
    try:
        privileged.delete_repo(REPO_NAME)
    except FileNotFoundError:
        pass

    privileged.create_repo(name=REPO_NAME, description='', owner='',
                           keep_ownership=True, is_private=True)


@git_installed
def test_create_repo():
    """Test creating a repository."""
    privileged.create_repo(name=REPO_NAME, description='', owner='',
                           is_private=True, keep_ownership=True)
    repo = privileged.repo_info(REPO_NAME)
    default_branch = repo.pop('default_branch')

    assert repo == REPO_DATA
    assert default_branch


@git_installed
def test_change_repo_medatada(existing_repo):
    """Test change a metadata of the repository."""
    new_data = {
        'name': REPO_NAME,
        'description': 'description2',
        'owner': 'owner2',
        'access': 'public',
    }

    privileged.set_repo_description(REPO_NAME, new_data['description'])
    privileged.set_repo_owner(REPO_NAME, new_data['owner'])
    privileged.set_repo_access(REPO_NAME, new_data['access'])
    repo = privileged.repo_info(REPO_NAME)
    del repo['default_branch']

    assert repo == new_data


@git_installed
def test_rename_repository(existing_repo):
    """Test renaming a repository."""
    new_name = 'Test-repo_2'

    privileged.rename_repo(REPO_NAME, new_name)
    with pytest.raises(RuntimeError, match='Repository not found'):
        privileged.repo_info(REPO_NAME)

    repo = privileged.repo_info(new_name)
    assert repo['name'] == new_name


@git_installed
def test_get_branches(existing_repo):
    """Test  getting all the branches of the repository."""
    result = privileged.get_branches(REPO_NAME)

    assert 'default_branch' in result
    assert result['branches'] == []


@git_installed
def test_delete_repository(existing_repo):
    """Test deleting a repository."""
    privileged.delete_repo(REPO_NAME)

    with pytest.raises(RuntimeError, match='Repository not found'):
        privileged.repo_info(REPO_NAME)


@pytest.mark.parametrize(
    'name',
    ['.Test-repo', 'Test-repo.git.git', '/root/Test-repo', 'Test-repö'])
def test_action_create_repo_with_invalid_names(name):
    """Test that creating repository with invalid names fails."""
    with pytest.raises(ValidationError):
        privileged.create_repo(name=name, description='', owner='',
                               keep_ownership=True)


@pytest.mark.parametrize('url', [
    'Test-repo', 'file://root/Test-repo', 'localhost/Test-repo',
    'ssh://localhost/Test-repo', 'https://localhost/.Test-repo'
])
def test_action_create_repo_with_invalid_urls(url):
    """Test that cloning repository with invalid URL fails."""
    with pytest.raises(ValidationError):
        privileged.create_repo(url=url, description='', owner='',
                               keep_ownership=True)
