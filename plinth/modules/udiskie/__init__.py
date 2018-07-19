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
FreedomBox app for udiskie.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import service as service_module
from plinth.menu import main_menu

version = 1

managed_services = ['freedombox-udiskie']

managed_packages = ['udiskie', 'gir1.2-udisks-2.0']

name = _('udiskie')

short_description = _('Removable Media')

description = [
    _('udiskie allows automatic mounting of removable media, such as flash '
      'drives.'),
]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-floppy-disk', 'udiskie:index',
                     short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], name, ports=[], is_external=False,
            is_enabled=is_enabled, enable=enable, disable=disable,
            is_running=is_running)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages, skip_recommends=True)
    helper.call('post', actions.superuser_run, 'udiskie', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], name, ports=[], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable,
            is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('freedombox-udiskie')


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('freedombox-udiskie')


def enable():
    """Enable the module."""
    actions.superuser_run('udiskie', ['enable'])


def disable():
    """Disable the module."""
    actions.superuser_run('udiskie', ['disable'])
