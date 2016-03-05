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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for upgrades
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import cfg


version = 1

is_essential = True

depends = ['system']

title = _('Software Upgrades')

description = [
    _('Upgrades install the latest software and security updates. When '
      'automatic upgrades are enabled, upgrades are automatically run every '
      'night. You don\'t normally need to start the upgrade process.')
]


def init():
    """Initialize the module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(title, 'glyphicon-refresh', 'upgrades:index', 21)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['unattended-upgrades'])
    helper.call('post', actions.superuser_run, 'upgrades', ['enable-auto'])


def get_status():
    """Return the current status."""
    return {'auto_upgrades_enabled': 'is_enabled'}


def is_enabled():
    """Return whether the module is enabled."""
    output = actions.run('upgrades', ['check-auto'])
    return 'True' in output.split()


def enable(should_enable):
    """Enable/disable the module."""
    option = 'enable-auto' if should_enable else 'disable-auto'
    actions.superuser_run('upgrades', [option])
