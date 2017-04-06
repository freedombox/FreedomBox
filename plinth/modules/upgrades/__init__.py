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
from plinth import service as service_module
from plinth.menu import main_menu


version = 1

is_essential = True

managed_packages = ['unattended-upgrades']

title = _('Software Upgrades')

description = [
    _('Upgrades install the latest software and security updates. When '
      'automatic upgrades are enabled, upgrades are automatically run every '
      'night. You don\'t normally need to start the upgrade process.')
]

service = None


def init():
    """Initialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-refresh', 'upgrades:index')
    global service
    service = service_module.Service(
        'auto-upgrades', title, is_external=False, is_enabled=is_enabled,
        enable=enable, disable=disable)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'upgrades', ['enable-auto'])


def is_enabled():
    """Return whether the module is enabled."""
    output = actions.run('upgrades', ['check-auto'])
    return 'True' in output.split()


def enable():
    """Enable the module."""
    actions.superuser_run('upgrades', ['enable-auto'])


def disable():
    """Disable the module."""
    actions.superuser_run('upgrades', ['disable-auto'])
