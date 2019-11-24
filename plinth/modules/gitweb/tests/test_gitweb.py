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
Test module for gitweb module operations.
"""

import imp
import json
import pathlib
from unittest.mock import patch

import pytest
from django.forms import ValidationError


def _action_file():
    """Return the path to the 'gitweb' actions file."""
    current_directory = pathlib.Path(__file__).parent
    return str(
        current_directory / '..' / '..' / '..' / '..' / 'actions' / 'gitweb')


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


def test_actions(call_action):
    """Test gitweb actions script."""
    repo = 'Test-repo'
    repo_renamed = 'Test-repo_2'
    data = {
        'name': repo,
        'description': 'Test description',
        'owner': 'Test owner',
        'access': 'private'
    }

    # Create repository
    call_action([
        'create-repo', '--name', repo, '--description', data['description'],
        '--owner', data['owner'], '--is-private', '--keep-ownership'
    ])
    assert json.loads(call_action(['repo-info', '--name', repo])) == data

    # Change metadata
    data['description'] = 'Test description 2'
    data['owner'] = 'Test owner 2'
    data['access'] = 'public'
    call_action([
        'set-repo-description', '--name', repo, '--description',
        data['description']
    ])
    call_action(['set-repo-owner', '--name', repo, '--owner', data['owner']])
    call_action(
        ['set-repo-access', '--name', repo, '--access', data['access']])
    assert json.loads(call_action(['repo-info', '--name', repo])) == data

    # Rename repository
    call_action(['rename-repo', '--oldname', repo, '--newname', repo_renamed])
    with pytest.raises(RuntimeError, match='Repository not found'):
        call_action(['repo-info', '--name', repo])
    assert call_action(['repo-info', '--name', repo_renamed])

    # Delete repository
    call_action(['delete-repo', '--name', repo_renamed])
    with pytest.raises(RuntimeError, match='Repository not found'):
        call_action(['repo-info', '--name', repo_renamed])


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
