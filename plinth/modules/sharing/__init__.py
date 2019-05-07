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
FreedomBox app to configure sharing.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import actions, cfg
from plinth.menu import main_menu
from plinth.utils import format_lazy

from .manifest import backup

version = 1

name = _('Sharing')

description = [
    format_lazy(
        _('Sharing allows you to share files and folders on your {box_name} '
          'over the web with chosen groups of users.'), box_name=_(
              cfg.box_name))
]


def init():
    """Initialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'sharing', 'sharing:index')
    menu.promote_item('sharing:index')


def list_shares():
    """Return a list of shares."""
    output = actions.superuser_run('sharing', ['list'])
    return json.loads(output)['shares']


def add_share(name, path, groups):
    """Add a new share by called the action script."""
    actions.superuser_run(
        'sharing',
        ['add', '--name', name, '--path', path, '--groups'] + groups)


def remove_share(name):
    """Remove a share by calling the action script."""
    actions.superuser_run('sharing', ['remove', '--name', name])
