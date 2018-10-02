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
Plinth module to configure coquelicot.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, frontpage
from plinth.menu import main_menu

from .manifest import backup, clients

clients = clients

version = 1

managed_services = ['coquelicot']

managed_packages = ['coquelicot']

name = _('Coquelicot')

short_description = _('File Sharing')

description = [
    _('Coquelicot is a “one-click” file sharing web application with a focus '
      'on protecting users’ privacy. It is best used for quickly sharing a '
      'single file. '),
    _('This Coquelicot instance is exposed to the public but requires an '
      'upload password to prevent unauthorized access. You can set a new '
      'upload password in the form that will appear below after installation. '
      'The default upload password is "test".')
]

service = None

manual_page = 'Coquelicot'


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'coquelicot', 'coquelicot:index',
                     short_description)

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
    helper.call('post', actions.superuser_run, 'coquelicot', ['setup'])
    helper.call('post', actions.superuser_run, 'coquelicot', ['enable'])
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
    frontpage.add_shortcut('coquelicot', name,
                           short_description=short_description,
                           url='/coquelicot', login_required=True)


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('coquelicot')


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('coquelicot')
            and action_utils.webserver_is_enabled('coquelicot-freedombox'))


def enable():
    """Enable the module."""
    actions.superuser_run('coquelicot', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('coquelicot', ['disable'])
    frontpage.remove_shortcut('coquelicot')


def get_current_max_file_size():
    """Get the current value of maximum file size."""
    size = actions.superuser_run('coquelicot', ['get-max-file-size'])
    return int(size.strip())


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/coquelicot',
                                         check_certificate=False))

    return results
