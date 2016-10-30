#
# This file is part of Plinth.
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
Plinth module for first boot wizard
"""

version = 1

is_essential = True
first_boot_steps = [{'id': 'firstboot_state0',
                     'url': 'first_boot:state0',
                     'order': 0
                     },
                     {'id': 'firstboot_state10',
                     'url': 'first_boot:state10',
                     'order': 10
                     }
                    ]
