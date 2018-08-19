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
Test module to exercise group registration.

It is recommended to run this module with root privileges in a virtual machine.
"""

import unittest
from plinth.modules import users


class TestGroups(unittest.TestCase):
    """Test groups behavior."""
    def test_register_group(self):
        """Test for multi addition of same group"""
        users.groups = dict()  # reset groups
        group = ('TestGroup', 'Group for testing')
        users.register_group(group)
        users.register_group(group)
        self.assertEqual(
            len(users.groups), 1,
            'Duplicate entries for same group generated!')
        return users.groups
