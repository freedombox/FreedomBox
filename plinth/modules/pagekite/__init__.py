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
Plinth module to configure PageKite
"""

from django.utils.translation import ugettext_lazy as _
from plinth import cfg

from . import utils

version = 1

depends = ['apps', 'names']

title = _('Public Visibility (PageKite)')


def init():
    """Intialize the PageKite module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-flag', 'pagekite:index', 800)

    # Register kite name with Name Services module.
    utils.update_names_module(initial_registration=True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['pagekite'])
