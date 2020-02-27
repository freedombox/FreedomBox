#!/usr/bin/python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module to exercise user actions.

it is recommended to run this module with root privileges in a virtual machine.
"""

import pathlib
import random
import re
import string
import subprocess

import pytest

from plinth import action_utils
from plinth.modules import security

_cleanup_users = None
_cleanup_groups = None

pytestmark = pytest.mark.usefixtures('needs_root', 'load_cfg')


def _random_string(length=8):
    """Return a random string created from lower case ascii."""
    return ''.join(
        [random.choice(string.ascii_lowercase) for _ in range(length)])


def _is_exit_zero(args):
    """Return whether a command gave exit code zero"""
    process = subprocess.run(args, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, check=False)
    return process.returncode == 0


def _get_password_hash(username):
    """Query and return the password hash of the given LDAP username"""
    query = [
        'ldapsearch', '-L', '-L', '-L', '-Y', 'EXTERNAL', '-H', 'ldapi:///',
        '-b', 'ou=users,dc=thisbox', '-Q', '(cn={})'.format(username),
        'userPassword'
    ]
    process = subprocess.run(query, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, check=True)
    return process.stdout.decode().strip().split()[-1]


def _get_samba_users():
    """Get users from the Samba user database."""
    stdout = subprocess.check_output(
        ['tdbdump', '/var/lib/samba/private/passdb.tdb']).decode()
    return re.findall(r'USER_(.*)\\0', stdout)


def _try_login_to_ssh(username, password, returncode=0):
    """Return whether the sshpass returncode matches when trying to
    login to ssh using the given username and password"""
    if not action_utils.service_is_running('ssh'):
        return True

    command = [
        'sshpass', '-p', password, 'ssh', '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'StrictHostKeyChecking=no', '-o', 'VerifyHostKeyDNS=no',
        username + '@127.0.0.1', '/bin/true'
    ]
    process = subprocess.run(command, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, check=False)
    return process.returncode == returncode


def _action_file():
    """Return the path to the 'users' actions file."""
    current_directory = pathlib.Path(__file__).parent
    return str(
        current_directory / '..' / '..' / '..' / '..' / 'actions' / 'users')


@pytest.fixture(name='disable_restricted_access', autouse=True)
def fixture_disable_restricted_access(needs_root, load_cfg):
    """Disable console login restrictions."""
    restricted_access = security.get_restricted_access_enabled()
    if restricted_access:
        security.set_restricted_access(False)
        yield
        security.set_restricted_access(True)
    else:
        yield


@pytest.fixture(name='auto_cleanup_users_groups', autouse=True)
def fixture_auto_cleanup_users_groups(needs_root, load_cfg):
    """Remove all the users and groups created during tests."""
    global _cleanup_users, _cleanup_groups

    _cleanup_users = set()
    _cleanup_groups = set()
    yield

    for user in _cleanup_users:
        try:
            _delete_user(user)
        except Exception:
            pass

    for group in _cleanup_groups:
        _delete_group(group)


def _call_action(arguments, **kwargs):
    """Call the action script."""
    kwargs['stdout'] = kwargs.get('stdout', subprocess.DEVNULL)
    kwargs['stderr'] = kwargs.get('stderr', subprocess.DEVNULL)
    kwargs['check'] = kwargs.get('check', True)
    return subprocess.run([_action_file()] + arguments, **kwargs)


def _create_user(username=None, groups=None):
    """Call the action script for creating a new user."""
    username = username or _random_string()
    password = _random_string()

    _call_action(['create-user', username], input=password.encode())

    if groups:
        for group in groups:
            _call_action(['add-user-to-group', username, group])
            if group != 'admin':
                _cleanup_groups.add(group)

    _cleanup_users.add(username)
    return username, password


def _delete_user(username):
    """Utility to delete an LDAP and Samba user"""
    _call_action(['remove-user', username])


def _rename_user(old_username, new_username=None):
    """Rename a user."""
    new_username = new_username or _random_string()
    _call_action(['rename-user', old_username, new_username])
    _cleanup_users.remove(old_username)
    _cleanup_users.add(new_username)
    return new_username


def _get_user_groups(username):
    """Return the list of groups for a user."""
    process = _call_action(['get-user-groups', username],
                           stdout=subprocess.PIPE)
    return process.stdout.decode().split()


def _create_group(groupname=None):
    groupname = groupname or _random_string()
    _call_action(['create-group', groupname])
    _cleanup_groups.add(groupname)
    return groupname


def _delete_group(groupname):
    _call_action(['remove-group', groupname])


def test_create_user():
    """Test whether creating a new user works."""
    username, password = _create_user(groups=['admin', _random_string()])
    # assert_can_login_to_console(username, password)
    assert _try_login_to_ssh(username, password)
    assert username in _get_samba_users()
    with pytest.raises(subprocess.CalledProcessError):
        _create_user(username)


def test_change_user_password():
    """Test changing user password."""
    username, old_password = _create_user(groups=['admin'])
    old_password_hash = _get_password_hash(username)
    new_password = 'pass $123'
    _call_action(['set-user-password', username], input=new_password.encode())
    new_password_hash = _get_password_hash(username)
    assert old_password_hash != new_password_hash

    # User can login to ssh using new password but not the old password.
    # sshpass gives a return code of 5 if the password is incorrect.
    assert _try_login_to_ssh(username, old_password, returncode=5)
    assert _try_login_to_ssh(username, new_password)


def test_set_password_for_non_existent_user():
    """Test setting password for a non-existent user."""
    non_existent_user = _random_string()
    fake_password = _random_string().encode()
    with pytest.raises(subprocess.CalledProcessError):
        _call_action(['set-user-password', non_existent_user],
                     input=fake_password)


def test_rename_user():
    """Test whether renaming a user works."""
    old_username, password = _create_user(groups=['admin', _random_string()])
    old_groups = _get_user_groups(old_username)

    new_username = _rename_user(old_username)
    assert _try_login_to_ssh(new_username, password)
    assert _try_login_to_ssh(old_username, password, returncode=5)
    assert old_username not in _get_samba_users()

    new_groups = _get_user_groups(new_username)
    old_users_groups = _get_user_groups(old_username)
    assert not old_users_groups  # empty
    assert old_groups == new_groups

    with pytest.raises(subprocess.CalledProcessError):
        _rename_user(old_username)

    # Renaming a non-existent user fails
    random_username = _random_string()
    with pytest.raises(subprocess.CalledProcessError):
        _rename_user(random_username, new_username=_random_string())

    # Renaming to an existing user fails
    existing_user, _ = _create_user()
    with pytest.raises(subprocess.CalledProcessError):
        _rename_user(existing_user, new_username=new_username)


def test_delete_user():
    """Test to check whether LDAP users can be deleted"""
    username, password = _create_user(groups=[_random_string()])
    _delete_user(username)
    groups_after = _get_user_groups(username)
    assert not groups_after  # User gets removed from all groups

    # User account cannot be found after deletion
    assert not _is_exit_zero(['ldapid', username])

    # Deleted user cannot login to ssh
    assert _try_login_to_ssh(username, password, returncode=5)

    assert username not in _get_samba_users()


def test_delete_non_existent_user():
    """Deleting a non-existent user should fail."""
    non_existent_user = _random_string()
    with pytest.raises(subprocess.CalledProcessError):
        _call_action(['delete-user', non_existent_user])


def test_groups():
    """Test to check that LDAP groups can be deleted"""
    groupname = _random_string()

    _create_group(groupname)
    assert _is_exit_zero(['ldapgid', groupname])

    # create-group is idempotent
    assert _is_exit_zero([_action_file(), 'create-group', groupname])

    _delete_group(groupname)
    assert not _is_exit_zero(['ldapgid', groupname])

    # delete-group is idempotent
    assert _is_exit_zero([_action_file(), 'remove-group', groupname])


def test_user_group_interactions():
    """Test adding/removing user from a groups."""
    group1 = _random_string()
    user1, _ = _create_user(groups=[group1])
    assert [group1] == _get_user_groups(user1)

    # add-user-to-group is not idempotent
    with pytest.raises(subprocess.CalledProcessError):
        _call_action(['add-user-to-group', user1, group1])

    # The same user can be added to other new groups
    group2 = _random_string()
    _create_group(group2)
    _call_action(['add-user-to-group', user1, group2])

    # Adding a user to a non-existent group creates the group
    group3 = _random_string()
    _call_action(['add-user-to-group', user1, group3])
    _cleanup_groups.add(group3)

    # The expected groups got created and the user is part of them.
    expected_groups = [group1, group2, group3]
    assert expected_groups == _get_user_groups(user1)

    # Remove user from group
    group_to_remove_from = random.choice(expected_groups)
    _call_action(['remove-user-from-group', user1, group_to_remove_from])

    # User is no longer in the group that they're removed from
    expected_groups.remove(group_to_remove_from)
    assert expected_groups == _get_user_groups(user1)

    # User cannot be removed from a group that they're not part of
    random_group = _random_string()
    _create_group(random_group)
    with pytest.raises(subprocess.CalledProcessError):
        _call_action(['remove-user-from-group', user1, random_group])
