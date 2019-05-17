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
FreedomBox app to configure Mumble server.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth import service as service_module
from plinth.views import ServiceView

from .manifest import backup, clients

version = 1

name = _('Mumble')

short_description = _('Voice Chat')

service = None

managed_services = ['mumble-server']

managed_packages = ['mumble-server']

description = [
    _('Mumble is an open source, low-latency, encrypted, high quality '
      'voice chat software.'),
    _('You can connect to your Mumble server on the regular Mumble port '
      '64738. <a href="http://mumble.info">Clients</a> to connect to Mumble '
      'from your desktop and Android devices are available.')
]

clients = clients

reserved_usernames = ['mumble-server']

manual_page = 'Mumble'

port_forwarding_info = [
    ('TCP', 64738),
    ('UDP', 64738),
]

app = None


class MumbleApp(app_module.App):
    """FreedomBox app for Mumble."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-mumble', name, short_description, 'mumble',
                              'mumble:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-mumble', name, short_description=short_description,
            icon='mumble', description=description,
            configure_url=reverse_lazy('mumble:index'), clients=clients)
        self.add(shortcut)


def init():
    """Intialize the Mumble module."""
    global app
    app = MumbleApp()

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'mumble-plinth'
        ], is_external=True, enable=enable, disable=disable)

        if service.is_enabled():
            app.set_enabled(True)


class MumbleServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "mumble"
    description = description
    clients = clients
    manual_page = manual_page
    port_forwarding_info = port_forwarding_info


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'mumble-plinth'
        ], is_external=True, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', app.enable)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    app.enable()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    app.disable()


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(64738, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp6'))

    return results
