# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module to exercise group registration.

It is recommended to run this module with root privileges in a virtual machine.
"""

from plinth.modules import users


def test_register_group():
    """Test for multi addition of same group"""
    users.groups = dict()  # reset groups
    group = ('TestGroup', 'Group for testing')
    users.register_group(group)
    users.register_group(group)
    assert len(users.groups) == 1
    return users.groups
