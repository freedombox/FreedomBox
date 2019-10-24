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

from plinth import action_utils
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.views import AppView

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

name = _('Mumble')

short_description = _('Voice Chat')

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

    app_id = 'mumble'

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

        firewall = Firewall('firewall-mumble', name, ports=['mumble-plinth'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-mumble', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the Mumble module."""
    global app
    app = MumbleApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


class MumbleAppView(AppView):
    app_id = 'mumble'
    diagnostics_module_name = 'mumble'
    name = name
    description = description
    clients = clients
    manual_page = manual_page
    port_forwarding_info = port_forwarding_info


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(64738, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp6'))

    return results
