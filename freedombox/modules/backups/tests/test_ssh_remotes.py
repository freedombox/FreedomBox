# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for SSH remotes for backups.
"""

import datetime
import os
import pwd
import subprocess

import pytest
from django.forms import ValidationError

from plinth.utils import generate_password, random_string

from .. import forms

pytestmark = [
    pytest.mark.usefixtures('needs_root', 'load_cfg', 'has_ssh_key'),
    pytest.mark.django_db
]


@pytest.fixture(name='temp_home', scope='module')
def fixture_temp_home_directory(needs_root):
    """Create a new temporary directory to act as a home directory.
    """
    # TODO Try to get this working with tempfile.TemporaryDirectory()
    dir_name = os.path.join('/tmp', random_string())
    yield dir_name
    os.path.exists(dir_name) and subprocess.check_call(['rm', '-rf', dir_name])


@pytest.fixture(name='password', scope='module')
def fixture_password():
    return generate_password()


def get_hashed_password(password):
    res = subprocess.run(['mkpasswd', '--method=md5', password],
                         stdout=subprocess.PIPE, check=True)
    return res.stdout.decode().strip()


@pytest.fixture(name='temp_user', scope='module')
def fixture_create_temp_user(temp_home, password, needs_root):
    """Create a temporary user.
    """
    username = random_string()
    hashed_password = get_hashed_password(password)
    # User account expires tomorrow
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    subprocess.check_call([
        'useradd', '-d', temp_home, '-m', '-e',
        tomorrow.strftime('%Y-%m-%d'), '-p', hashed_password, username
    ])
    yield username
    subprocess.check_call(['sudo', 'pkill', '-u', username])
    subprocess.check_call(['sudo', 'userdel', username])


@pytest.fixture(name='has_ssh_key', scope='module', autouse=True)
def fixture_ssh_key(temp_home, temp_user, password, needs_root, needs_sudo):
    subprocess.check_call([
        'sudo', '-n', '-u', temp_user, 'ssh-keygen', '-t', 'rsa', '-b', '1024',
        '-N', '', '-f', f'{temp_home}/.ssh/id_rsa', '-q'
    ])


@pytest.mark.skip
def test_user_setup(temp_home, temp_user):
    assert os.path.isdir(temp_home)
    assert pwd.getpwnam(temp_user)


@pytest.mark.skip
def test_add_repository_when_directory_is_missing(temp_user, temp_home,
                                                  password):
    remote_path = os.path.join(temp_home, 'non_existent_dir')
    data = {
        'repository': f'{temp_user}@localhost:{remote_path}',
        'ssh_password': password,
        'encryption': 'none'
    }
    # TODO test the view instead of the form
    form = forms.AddRemoteRepositoryForm(data=data)
    form.is_valid()
    assert os.path.isdir(remote_path)  # Directory gets created


@pytest.mark.skip
def test_add_repository_when_directory_exists_and_empty(
        temp_user, temp_home, password):
    remote_path = os.path.join(temp_home, 'empty_dir')
    os.makedirs(remote_path)
    data = {
        'repository': f'{temp_user}@localhost:{remote_path}',
        'ssh_password': password,
        'encryption': 'none'
    }
    # TODO test the view instead of the form
    form = forms.AddRemoteRepositoryForm(data=data)
    form.is_valid()


# TODO Fails only in unit test but not if manually tested!
@pytest.mark.skip
def test_add_repository_when_directory_exists_and_not_empty(
        temp_user, temp_home, password):
    remote_path = os.path.join(temp_home, 'non_empty_dir')
    os.makedirs(remote_path)
    open(os.path.join(remote_path, 'somefile.txt'), 'w',
         encoding='utf-8').close()
    data = {
        'repository': f'{temp_user}@localhost:{remote_path}',
        'ssh_password': password,
        'encryption': 'none'
    }
    form = forms.AddRemoteRepositoryForm(data=data)
    with pytest.raises(ValidationError):
        form.is_valid()
