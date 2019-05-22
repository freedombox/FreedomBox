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
Tests for SSH remotes for backups.
"""

import datetime
import os
import pwd
import shutil
import subprocess
import tempfile

import pytest

from plinth.utils import generate_password, random_string

from .. import forms

pytestmark = pytest.mark.usefixtures('needs_root')


@pytest.fixture(name='temp_home', scope='module', autouse=True)
def fixture_temp_home_directory():
    """Create a new temporary directory to act as a home directory.
    """
    # TODO Try to get this working with tempfile.TemporaryDirectory()
    tempfile.TemporaryDirectory()
    dir_name = f'/tmp/{random_string()}'
    os.mkdir(dir_name)
    yield dir_name
    subprocess.check_call(['rm', '-rf', dir_name])


@pytest.fixture(name='password', scope='module', autouse=True)
def fixture_password():
    return generate_password()


@pytest.fixture(name='temp_user', scope='module', autouse=True)
def fixture_create_temp_user(temp_home, password):
    """Create a temporary user.
    """
    username = random_string()
    # User account expires tomorrow
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    subprocess.check_call([
        'useradd', '-d', temp_home, '-m', '-p', password, username, '-e',
        tomorrow.strftime('%Y-%m-%d')
    ])
    subprocess.check_call(['chown', username, temp_home])
    yield username
    subprocess.check_call(['userdel', username])


@pytest.mark.usefixtures('needs_sudo')
@pytest.fixture(name='has_ssh_key', scope='module', autouse=True)
def fixture_ssh_key(temp_home, temp_user, password):
    subprocess.check_call([
        'sudo', '-n', '-u', temp_user, 'ssh-keygen', '-t', 'rsa', '-b', '1024',
        '-N', '', '-f', f'{temp_home}/.ssh/id_rsa', '-q'
    ])


@pytest.mark.skip
@pytest.mark.usefixtures('has_ssh_key')
def test_user_setup(temp_home, temp_user):
    assert os.path.isdir(temp_home)
    assert pwd.getpwnam(temp_user)


# Tests
# forms.AddRepositoryForm
#  *  Create empty directory if not exists
#     * Check if the directory is empty
#       - if not empty, check if it's an existing backup repository
#       - else throw an error


@pytest.mark.skip
@pytest.mark.django_db
@pytest.mark.usefixtures('has_ssh_key')
def test_add_repository_when_directory_is_missing(temp_home, temp_user,
                                                  password):
    repo_path = os.path.join(temp_home, 'backups')
    data = {
        'repository': f'{temp_user}@localhost:{repo_path}',
        'ssh_password': password,
        'encryption': 'none'
    }
    form = forms.AddRepositoryForm(data=data)
    form.is_valid()
    form.clean()
    assert os.path.isdir(repo_path)
