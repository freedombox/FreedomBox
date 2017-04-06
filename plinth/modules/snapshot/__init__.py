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
Plinth module to manage filesystem snapshots.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.menu import main_menu


version = 1

managed_packages = ['snapper']

title = _('Snapshots')

description = [
    _('Snapshots allows creating and managing filesystem snapshots. These can '
      'be used to roll back the system to a previously known good state in '
      'case of unwanted changes to the system.'),

    _('Automatic snapshots are taken every hour, day, month and year. Older '
      'snapshots are automatically deleted keeping 10 of each kind and 50 in '
      'total. Although snapshots are efficient and only store the '
      'differences, they may be deleted to reclaim free space.  Individual '
      'files from older snapshots can be accessed by visiting ".snapshots" '
      'directory in the filesystem. Snapshots are not a replacement for '
      'backups.')
]

service = None


def init():
    """Initialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-film', 'snapshot:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'snapshot', ['setup'])
