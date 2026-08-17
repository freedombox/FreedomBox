# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for the UsersAndGroups app component.
"""

import pytest

from ..components import UsersAndGroups


@pytest.fixture(autouse=True)
def fixture_empty_components():
    """Remove all components from the global list before every test."""
    UsersAndGroups._all_components = set()


def test_create_users_and_groups_component():
    """Test initialization of users and groups component."""
    component = UsersAndGroups('simple-component')
    assert component.groups == {}
    assert component.reserved_usernames == []
    assert len(component._all_components) == 1
    assert component in component._all_components

    groups = {'test-group1', 'Test description'}
    component = UsersAndGroups('another-component', groups=groups,
                               reserved_usernames=['test-user1'])
    assert component.groups == groups
    assert component.reserved_usernames == ['test-user1']
    assert len(component._all_components) == 2
    assert component in component._all_components


def test_get_groups():
    """Test getting all the groups.

    Test that:
    1. Group names are unique
    2. All components have the same global set of groups

    """
    UsersAndGroups('component-with-no-groups')
    UsersAndGroups('component-with-one-group',
                   groups={'group1': 'description1'})
    UsersAndGroups('component-with-groups', groups={
        'group1': 'description1',
        'group2': 'description2'
    })

    assert UsersAndGroups.get_groups() == {'group1', 'group2'}
    assert UsersAndGroups.get_group_choices() == [
        ('group1', 'description1 (group1)'),
        ('group2', 'description2 (group2)')
    ]


def test_check_username_reservation():
    """Test username reservations by multiple components."""
    UsersAndGroups('complex-component',
                   reserved_usernames=['username1', 'username2'],
                   groups={'somegroup', 'some description'})
    assert not UsersAndGroups.is_username_reserved('something')
    assert UsersAndGroups.is_username_reserved('username1')

    assert not UsersAndGroups.is_username_reserved('username3')
    UsersAndGroups('temp-component', reserved_usernames=['username3'])
    assert UsersAndGroups.is_username_reserved('username3')
