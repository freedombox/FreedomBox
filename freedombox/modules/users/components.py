# SPDX-License-Identifier: AGPL-3.0-or-later
"""
App component to manage users and groups.
"""

import itertools
from typing import ClassVar

from plinth import app


class UsersAndGroups(app.FollowerComponent):
    """Component to manage users and groups of an app."""

    # Class variable to hold a list of user groups for apps
    _all_components: ClassVar[set['UsersAndGroups']] = set()

    def __init__(self, component_id, reserved_usernames=[], groups={}):
        """Store reserved_usernames and groups of the app.

        'reserved_usernames' is a list of operating system user names that the
        app uses. It is not permitted to create a FreedomBox user with one of
        these names.

        'groups' is a dictionary of the following format: {"group_name": "A
        localized string describing what permissions are offered to the users
        of this group"}.

        """
        super().__init__(component_id)

        self.reserved_usernames = reserved_usernames
        self.groups = groups

        self._all_components.add(self)

    @classmethod
    def get_groups(cls):
        """Return a set of all groups."""
        all_groups = itertools.chain(*(component.groups.keys()
                                       for component in cls._all_components))
        return set(all_groups)

    @classmethod
    def get_group_choices(cls):
        """Return list of groups that can be used as form choices."""
        all_groups = itertools.chain(*(component.groups.items()
                                       for component in cls._all_components))
        choices = [(group, f'{description} ({group})')
                   for group, description in set(all_groups)]
        return sorted(choices, key=lambda g: g[0])

    @classmethod
    def is_username_reserved(cls, username):
        """Returns whether the given username is reserved or not."""
        return any((username in component.reserved_usernames
                    for component in cls._all_components))
