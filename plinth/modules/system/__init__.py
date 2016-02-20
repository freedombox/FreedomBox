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
Plinth module for system section page
"""

from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy


version = 1

is_essential = True

title = _('System Configuration')

description = [
    format_lazy(
        _('Here you can administrate the underlying system of your '
          '{box_name}.'), box_name=_(cfg.box_name)),

    format_lazy(
        _('The options affect the {box_name} at its most general level, '
          'so be careful!'), box_name=_(cfg.box_name))
]


def init():
    """Initialize the system module"""
    cfg.main_menu.add_urlname(title, 'glyphicon-cog', 'system:index', 100)
