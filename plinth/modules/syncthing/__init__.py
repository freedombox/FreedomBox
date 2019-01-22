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
FreedomBox app to configure Syncthing.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, cfg, frontpage
from plinth.menu import main_menu
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

managed_services = ['syncthing@syncthing']

managed_packages = ['syncthing']

name = _('Syncthing')

short_description = _('File Synchronization')

description = [
    _('Syncthing is an application to synchronize files across multiple '
      'devices, e.g. your desktop computer and mobile phone.  Creation, '
      'modification, or deletion of files on one device will be automatically '
      'replicated on all other devices that also run Syncthing.'),
    format_lazy(
        _('Running Syncthing on {box_name} provides an extra synchronization '
          'point for your data that is available most of the time, allowing '
          'your devices to synchronize more often.  {box_name} runs a single '
          'instance of Syncthing that may be used by multiple users.  Each '
          'user\'s set of devices may be synchronized with a distinct set of '
          'folders.  The web interface on {box_name} is only available for '
          'users belonging to the "admin" group.'), box_name=_(cfg.box_name)),
    _('When enabled, Syncthing\'s web interface will be available from '
      '<a href="/syncthing/">/syncthing</a>.  Desktop and mobile clients are '
      'also <a href="https://syncthing.net/">available</a>.'),
]

clients = clients

group = ('syncthing', _('Administer Syncthing application'))

service = None

manual_page = 'Syncthing'


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'syncthing', 'syncthing:index',
                     short_description)
    register_group(group)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'syncthing', ['enable'])
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut('syncthing', name,
                           short_description=short_description,
                           url='/syncthing/', login_required=True,
                           allowed_groups=[group[0]])


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('syncthing@syncthing')


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('syncthing@syncthing')
            and action_utils.webserver_is_enabled('syncthing-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('syncthing', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('syncthing', ['disable'])
    frontpage.remove_shortcut('syncthing')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/syncthing/',
                                         check_certificate=False))

    return results
