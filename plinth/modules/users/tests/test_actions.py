#!/usr/bin/python3
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
Test module to exercise user actions.

it is recommended to run this module with root privileges in a virtual machine.
"""

import os
import random
import string
import subprocess
import unittest

from plinth import action_utils
from plinth.modules import security

euid = os.geteuid()


def random_string(length=8):
    """Return a random string created from lower case ascii."""
    return ''.join(
        [random.choice(string.ascii_lowercase) for _ in range(length)])


def is_exit_zero(args):
    """Return whether a command gave exit code zero"""
    process = subprocess.run(args, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, check=False)
    return process.returncode == 0


def get_password_hash(username):
    """Query and return the password hash of the given LDAP username"""
    query = [
        'ldapsearch', '-L', '-L', '-L', '-Y', 'EXTERNAL', '-H', 'ldapi:///',
        '-b', 'ou=users,dc=thisbox', '-Q', '(cn={})'.format(username),
        'userPassword'
    ]
    process = subprocess.run(query, stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, check=True)
    return process.stdout.decode().strip().split()[-1]


def try_login_to_ssh(username, password, returncode=0):
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


class TestActions(unittest.TestCase):
    """Test user related actions."""

    def setUp(self):
        """Setup each ."""
        current_directory = os.path.dirname(__file__)
        self.action_file = os.path.join(current_directory, '..', '..', '..',
                                        '..', 'actions', 'users')
        self.users = set()
        self.groups = set()
        self.restricted_access = security.get_restricted_access_enabled()
        if self.restricted_access:
            security.set_restricted_access(False)

    def tearDown(self):
        for user in self.users:
            try:
                self.delete_user(user)
            except Exception:
                pass

        for group in self.groups:
            self.delete_group(group)

        security.set_restricted_access(self.restricted_access)

    def call_action(self, arguments, **kwargs):
        """Call the action script."""
        kwargs['stdout'] = kwargs.get('stdout', subprocess.DEVNULL)
        kwargs['stderr'] = kwargs.get('stderr', subprocess.DEVNULL)
        kwargs['check'] = kwargs.get('check', True)
        return subprocess.run([self.action_file] + arguments, **kwargs)

    def create_user(self, username=None, groups=None):
        """Call the action script for creating a new user."""
        username = username or random_string()
        password = random_string()

        self.call_action(['create-user', username], input=password.encode())

        if groups:
            for group in groups:
                self.call_action(['add-user-to-group', username, group])
                self.groups.add(group)

        self.users.add(username)
        return username, password

    def delete_user(self, username):
        """Utility to delete an LDAP user"""
        self.call_action(['remove-user', username])

    def rename_user(self, old_username, new_username=None):
        """Rename a user."""
        new_username = new_username or random_string()
        self.call_action(['rename-user', old_username, new_username])
        self.users.remove(old_username)
        self.users.add(new_username)
        return new_username

    def get_user_groups(self, username):
        """Return the list of groups for a user."""
        process = self.call_action(['get-user-groups', username],
                                   stdout=subprocess.PIPE)
        return process.stdout.decode().split()

    def create_group(self, groupname=None):
        groupname = groupname or random_string()
        self.call_action(['create-group', groupname])
        self.groups.add(groupname)
        return groupname

    def delete_group(self, groupname):
        self.call_action(['remove-group', groupname])

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_create_user(self):
        """Test whether creating a new user works."""
        username, password = self.create_user(
            groups=['admin', random_string()])
        # assert_can_login_to_console(username, password)
        self.assertTrue(try_login_to_ssh(username, password))
        with self.assertRaises(subprocess.CalledProcessError):
            self.create_user(username)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_change_user_password(self):
        username, old_password = self.create_user(groups=['admin'])
        old_password_hash = get_password_hash(username)
        new_password = 'pass $123'
        self.call_action(['set-user-password', username],
                         input=new_password.encode())
        new_password_hash = get_password_hash(username)
        self.assertNotEqual(old_password_hash, new_password_hash)

        # User can login to ssh using new password but not the old password.
        # sshpass gives a return code of 5 if the password is incorrect.
        self.assertTrue(try_login_to_ssh(username, old_password, returncode=5))
        self.assertTrue(try_login_to_ssh(username, new_password))

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_set_password_for_non_existent_user(self):
        non_existent_user = random_string()
        fake_password = random_string().encode()
        with self.assertRaises(subprocess.CalledProcessError):
            self.call_action(['set-user-password', non_existent_user],
                             input=fake_password)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_rename_user(self):
        """Test whether renaming a user works."""
        old_username, password = self.create_user(
            groups=['admin', random_string()])
        old_groups = self.get_user_groups(old_username)

        new_username = self.rename_user(old_username)
        self.assertTrue(try_login_to_ssh(new_username, password))
        self.assertTrue(try_login_to_ssh(old_username, password, returncode=5))

        new_groups = self.get_user_groups(new_username)
        old_users_groups = self.get_user_groups(old_username)
        self.assertFalse(old_users_groups)  # empty
        self.assertEqual(old_groups, new_groups)

        with self.assertRaises(subprocess.CalledProcessError):
            self.rename_user(old_username)

        # Renaming a non-existent user fails
        random_username = random_string()
        with self.assertRaises(subprocess.CalledProcessError):
            self.rename_user(random_username, new_username=random_string())

        # Renaming to an existing user fails
        existing_user, _ = self.create_user()
        with self.assertRaises(subprocess.CalledProcessError):
            self.rename_user(existing_user, new_username=new_username)

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_delete_user(self):
        """Test to check whether LDAP users can be deleted"""
        username, password = self.create_user(groups=[random_string()])
        self.delete_user(username)
        groups_after = self.get_user_groups(username)
        self.assertFalse(groups_after)  # User gets removed from all groups

        # User account cannot be found after deletion
        self.assertFalse(is_exit_zero(['ldapid', username]))

        # Deleted user cannot login to ssh
        self.assertTrue(try_login_to_ssh(username, password, returncode=5))

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_delete_non_existent_user(self):
        """Deleting a non-existent user should fail."""
        non_existent_user = random_string()
        with self.assertRaises(subprocess.CalledProcessError):
            self.call_action(['delete-user', non_existent_user])

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_groups(self):
        """Test to check that LDAP groups can be deleted"""
        groupname = random_string()

        self.create_group(groupname)
        self.assertTrue(is_exit_zero(['ldapgid', groupname]))

        # create-group is idempotent
        self.assertTrue(
            is_exit_zero([self.action_file, 'create-group', groupname]))

        self.delete_group(groupname)
        self.assertFalse(is_exit_zero(['ldapgid', groupname]))

        # delete-group is idempotent
        self.assertTrue(
            is_exit_zero([self.action_file, 'remove-group', groupname]))

    @unittest.skipUnless(euid == 0, 'Needs to be root')
    def test_user_group_interactions(self):
        group1 = random_string()
        user1, _ = self.create_user(groups=[group1])
        self.assertEqual([group1], self.get_user_groups(user1))

        # add-user-to-group is not idempotent
        with self.assertRaises(subprocess.CalledProcessError):
            self.call_action(['add-user-to-group', user1, group1])

        # The same user can be added to other new groups
        group2 = random_string()
        self.create_group(group2)
        self.call_action(['add-user-to-group', user1, group2])

        # Adding a user to a non-existent group creates the group
        group3 = random_string()
        self.call_action(['add-user-to-group', user1, group3])
        self.groups.add(group3)

        # The expected groups got created and the user is part of them.
        expected_groups = [group1, group2, group3]
        self.assertEqual(expected_groups, self.get_user_groups(user1))

        # Remove user from group
        group_to_remove_from = random.choice(expected_groups)
        self.call_action(
            ['remove-user-from-group', user1, group_to_remove_from])

        # User is no longer in the group that they're removed from
        expected_groups.remove(group_to_remove_from)
        self.assertEqual(expected_groups, self.get_user_groups(user1))

        # User cannot be removed from a group that they're not part of
        random_group = random_string()
        self.create_group(random_group)
        with self.assertRaises(subprocess.CalledProcessError):
            self.call_action(['remove-user-from-group', user1, random_group])
