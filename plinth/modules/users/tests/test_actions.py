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
from plinth.tests import config as test_config

_cleanup_users = None
_cleanup_groups = None


def _is_ldap_set_up():
    """Return whether LDAP is set up."""
    try:
        return subprocess.call([
            'ldapsearch', '-Y', 'EXTERNAL', '-H', 'ldapi:///', '-b',
            'ou=groups,dc=thisbox'
        ]) == 0
    except FileNotFoundError:
        return False


pytestmark = [
    pytest.mark.usefixtures('needs_root', 'load_cfg'),
    pytest.mark.skipif(not _is_ldap_set_up(), reason="LDAP is not configured")
]


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
    return str(current_directory / '..' / '..' / '..' / '..' / 'actions' /
               'users')


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
    kwargs['stdout'] = kwargs.get('stdout', subprocess.PIPE)
    kwargs['stderr'] = kwargs.get('stderr', subprocess.PIPE)
    kwargs['check'] = kwargs.get('check', True)
    return subprocess.run([_action_file()] + arguments, **kwargs)


def _create_user(username=None, groups=None):
    """Call the action script for creating a new user."""
    username = username or _random_string()
    password = username + '_passwd'
    admin_user, admin_password = _get_admin_user_password()

    process_input = "{0}\n{1}".format(password, admin_password).encode()
    _call_action(['create-user', '--auth-user', admin_user, username],
                 input=process_input)

    if groups:
        for group in groups:
            admin_user, admin_password = _get_admin_user_password()
            _call_action([
                'add-user-to-group', '--auth-user', admin_user, username, group
            ], input=admin_password.encode())
            if group != 'admin':
                _cleanup_groups.add(group)

    _cleanup_users.add(username)
    return username, password


def _delete_user(username):
    """Utility to delete an LDAP and Samba user"""
    process_input = None
    if _get_group_users('admin') == [username]:
        _, admin_password = _get_admin_user_password()
        process_input = admin_password.encode()
    _call_action(['remove-user', username], input=process_input)


def _create_admin_if_does_not_exist():
    """Create a main admin user"""
    admin_user, _ = _get_admin_user_password()
    if not admin_user:
        username = "pytest_admin"
        _create_user(username, ['admin'])


def _get_admin_user_password():
    """Return an admin username and password."""

    admin_users = _get_group_users('admin')

    if not admin_users:
        return ('', '')

    if test_config.admin_username in admin_users:
        return (test_config.admin_username, test_config.admin_password)

    pytest_admin_username = 'pytest_admin'
    if pytest_admin_username in admin_users:
        return (pytest_admin_username, pytest_admin_username + '_passwd')

    return (admin_users[0], admin_users[0] + '_passwd')


def _rename_user(old_username, new_username=None):
    """Rename a user."""
    new_username = new_username or _random_string()

    _call_action(['rename-user', old_username, new_username])
    _cleanup_users.remove(old_username)
    _cleanup_users.add(new_username)
    return new_username


def _get_group_users(group):
    """Return the list of members in a group."""
    process = _call_action(['get-group-users', group])
    return process.stdout.decode().split()


def _get_user_groups(username):
    """Return the list of groups for a user."""
    process = _call_action(['get-user-groups', username])
    return process.stdout.decode().split()


def _create_group(groupname=None):
    groupname = groupname or _random_string()
    _call_action(['create-group', groupname])
    if groupname != 'admin':
        _cleanup_groups.add(groupname)
    return groupname


def _delete_group(groupname):
    _call_action(['remove-group', groupname])


def test_create_user():
    """Test whether creating a new user works."""
    _create_admin_if_does_not_exist()

    username, password = _create_user(groups=[_random_string()])

    assert _try_login_to_ssh(username, password)
    assert username in _get_samba_users()
    with pytest.raises(subprocess.CalledProcessError):
        _create_user(username)


def test_change_user_password():
    """Test changing user password."""
    _create_admin_if_does_not_exist()
    admin_user, admin_password = _get_admin_user_password()

    username, old_password = _create_user()
    old_password_hash = _get_password_hash(username)
    new_password = 'pass $123'

    process_input = "{0}\n{1}".format(new_password, admin_password).encode()
    _call_action(['set-user-password', username, '--auth-user', admin_user],
                 input=process_input)

    new_password_hash = _get_password_hash(username)
    assert old_password_hash != new_password_hash

    # User can login to ssh using new password but not the old password.
    # sshpass gives a return code of 5 if the password is incorrect.
    assert _try_login_to_ssh(username, old_password, returncode=5)
    assert _try_login_to_ssh(username, new_password)


def test_change_password_as_non_admin_user():
    """Test changing user password as a non-admin user."""
    _create_admin_if_does_not_exist()

    username, old_password = _create_user()
    old_password_hash = _get_password_hash(username)
    new_password = 'pass $123'

    process_input = "{0}\n{1}".format(new_password, old_password).encode()
    _call_action(['set-user-password', username, '--auth-user', username],
                 input=process_input)

    new_password_hash = _get_password_hash(username)
    assert old_password_hash != new_password_hash

    # User can login to ssh using new password but not the old password.
    # sshpass gives a return code of 5 if the password is incorrect.
    assert _try_login_to_ssh(username, old_password, returncode=5)
    assert _try_login_to_ssh(username, new_password)


def test_change_other_users_password_as_non_admin():
    """Test that changing other user's password as a non-admin user fails."""
    _create_admin_if_does_not_exist()

    username1, password1 = _create_user()
    username2, _ = _create_user()
    new_password = 'pass $123'

    process_input = "{0}\n{1}".format(new_password, password1).encode()
    with pytest.raises(subprocess.CalledProcessError):
        _call_action(
            ['set-user-password', username2, '--auth-user', username1],
            input=process_input)


def test_set_password_for_non_existent_user():
    """Test setting password for a non-existent user."""
    _create_admin_if_does_not_exist()
    admin_user, admin_password = _get_admin_user_password()

    non_existent_user = _random_string()
    fake_password = _random_string()

    process_input = "{0}\n{1}".format(fake_password, admin_password).encode()
    with pytest.raises(subprocess.CalledProcessError):
        _call_action([
            'set-user-password', non_existent_user, '--auth-user', admin_user
        ], input=process_input)


def test_rename_user():
    """Test whether renaming a user works."""
    _create_admin_if_does_not_exist()

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
    _create_admin_if_does_not_exist()

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


def test_delete_admin_group_fails():
    """Test that deleting the admin group fails."""
    groupname = 'admin'
    _create_group('admin')

    assert not _is_exit_zero([_action_file(), 'remove-group', groupname])


def test_user_group_interactions():
    """Test adding/removing user from a groups."""
    _create_admin_if_does_not_exist()
    admin_user, admin_password = _get_admin_user_password()

    group1 = _random_string()
    user1, _ = _create_user(groups=[group1])
    assert [group1] == _get_user_groups(user1)

    # add-user-to-group is not idempotent
    with pytest.raises(subprocess.CalledProcessError):
        _call_action(
            ['add-user-to-group', '--auth-user', admin_user, user1, group1],
            input=admin_password.encode())

    # The same user can be added to other new groups
    group2 = _random_string()
    _create_group(group2)
    _call_action(
        ['add-user-to-group', '--auth-user', admin_user, user1, group2],
        input=admin_password.encode())

    # Adding a user to a non-existent group creates the group
    group3 = _random_string()
    _call_action(
        ['add-user-to-group', '--auth-user', admin_user, user1, group3],
        input=admin_password.encode())
    _cleanup_groups.add(group3)

    # The expected groups got created and the user is part of them.
    expected_groups = [group1, group2, group3]
    assert expected_groups == _get_user_groups(user1)

    # Remove user from group
    group_to_remove_from = random.choice(expected_groups)
    _call_action([
        'remove-user-from-group', '--auth-user', admin_user, user1,
        group_to_remove_from
    ], input=admin_password.encode())

    # User is no longer in the group that they're removed from
    expected_groups.remove(group_to_remove_from)
    assert expected_groups == _get_user_groups(user1)

    # User cannot be removed from a group that they're not part of
    random_group = _random_string()
    _create_group(random_group)
    with pytest.raises(subprocess.CalledProcessError):
        _call_action([
            'remove-user-from-group', '--auth-user', admin_user, user1,
            random_group
        ], input=admin_password.encode())
