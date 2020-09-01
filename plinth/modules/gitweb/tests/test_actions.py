# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for gitweb module operations.
"""

import imp
import json
import pathlib
from unittest.mock import patch

import pytest
from django.forms import ValidationError

REPO_NAME = 'Test-repo'
REPO_DATA = {
    'name': REPO_NAME,
    'description': '',
    'owner': '',
    'access': 'private',
    'default_branch': 'master',
}


def _action_file():
    """Return the path to the 'gitweb' actions file."""
    current_directory = pathlib.Path(__file__).parent
    return str(current_directory / '..' / '..' / '..' / '..' / 'actions' /
               'gitweb')


gitweb_actions = imp.load_source('gitweb', _action_file())


@pytest.fixture(name='call_action')
def fixture_call_action(tmpdir, capsys):
    """Run actions with custom repo root path."""

    def _call_action(args, **kwargs):
        gitweb_actions.GIT_REPO_PATH = str(tmpdir)
        with patch('argparse._sys.argv', ['gitweb'] + args):
            gitweb_actions.main()
            captured = capsys.readouterr()
            return captured.out

    return _call_action


@pytest.fixture(name='existing_repo')
def fixture_existing_repo(call_action):
    """A fixture to create a repository."""
    try:
        call_action(['delete-repo', '--name', REPO_NAME])
    except FileNotFoundError:
        pass

    call_action([
        'create-repo', '--name', REPO_NAME, '--description', '', '--owner', '',
        '--is-private', '--keep-ownership'
    ])


def test_create_repo(call_action):
    """Test creating a repository."""
    call_action([
        'create-repo', '--name', REPO_NAME, '--description', '', '--owner', '',
        '--is-private', '--keep-ownership'
    ])

    assert json.loads(call_action(['repo-info', '--name',
                                   REPO_NAME])) == REPO_DATA


def test_change_repo_medatada(call_action, existing_repo):
    """Test change a metadata of the repository."""
    new_data = {
        'name': REPO_NAME,
        'description': 'description2',
        'owner': 'owner2',
        'access': 'public',
        'default_branch': 'master',
    }

    call_action([
        'set-repo-description', '--name', REPO_NAME, '--description',
        new_data['description']
    ])
    call_action(
        ['set-repo-owner', '--name', REPO_NAME, '--owner', new_data['owner']])
    call_action([
        'set-repo-access', '--name', REPO_NAME, '--access', new_data['access']
    ])

    assert json.loads(call_action(['repo-info', '--name',
                                   REPO_NAME])) == new_data


def test_rename_repository(call_action, existing_repo):
    """Test renaming a repository."""
    new_name = 'Test-repo_2'

    call_action(['rename-repo', '--oldname', REPO_NAME, '--newname', new_name])
    with pytest.raises(RuntimeError, match='Repository not found'):
        call_action(['repo-info', '--name', REPO_NAME])

    assert json.loads(call_action(['repo-info', '--name', new_name])) == {
        **REPO_DATA,
        **{
            'name': new_name
        }
    }


def test_get_branches(call_action, existing_repo):
    """Test  getting all the branches of the repository."""
    assert json.loads(call_action(['get-branches', '--name', REPO_NAME])) == {
        "default_branch": "master",
        "branches": []
    }


def test_delete_repository(call_action, existing_repo):
    """Test deleting a repository."""
    call_action(['delete-repo', '--name', REPO_NAME])

    with pytest.raises(RuntimeError, match='Repository not found'):
        call_action(['repo-info', '--name', REPO_NAME])


@pytest.mark.parametrize(
    'name',
    ['.Test-repo', 'Test-repo.git.git', '/root/Test-repo', 'Test-repö'])
def test_action_create_repo_with_invalid_names(call_action, name):
    """Test that creating repository with invalid names fails."""
    with pytest.raises(ValidationError):
        call_action([
            'create-repo', '--name', name, '--description', '', '--owner', '',
            '--keep-ownership'
        ])


@pytest.mark.parametrize('url', [
    'Test-repo', 'file://root/Test-repo', 'localhost/Test-repo',
    'ssh://localhost/Test-repo', 'https://localhost/.Test-repo'
])
def test_action_create_repo_with_invalid_urls(call_action, url):
    """Test that cloning repository with invalid URL fails."""
    with pytest.raises(ValidationError):
        call_action([
            'create-repo', '--url', url, '--description', '', '--owner', '',
            '--keep-ownership'
        ])
