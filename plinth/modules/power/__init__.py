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
Plinth module for power controls.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.menu import main_menu

version = 1

is_essential = True

title = _('Power')

description = [
    _('Restart or shut down the system.')
]


def init():
    """Initialize the power module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-off', 'power:index')
