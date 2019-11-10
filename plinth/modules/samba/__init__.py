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
FreedomBox app to configure samba.
"""

import socket

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_services = ['smbd']

managed_packages = ['samba']

name = _('Samba')

short_description = _('Samba File Sharing')

description = [
    _('Samba file sharing allows to share files between computers in your '
      'local network. '),
    format_lazy(
        _('If enabled, Samba share will be available at \\\\{hostname} on '
          'Windows and smb://{hostname} on Linux and Mac'),
        hostname=socket.gethostname()),
]

clients = clients

app = None


class SambaApp(app_module.App):
    """FreedomBox app for Samba file sharing."""

    app_id = 'samba'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-samba', name, short_description, 'samba',
                              'samba:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-samba', name, short_description=short_description,
            icon='samba', description=description,
            configure_url=reverse_lazy('samba:index'), clients=clients,
            login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-samba', name, ports=['samba'])
        self.add(firewall)

        daemon = Daemon('daemon-samba', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the module."""
    global app
    app = SambaApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'samba', ['setup'])
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(137, 'udp4'))
    results.append(action_utils.diagnose_port_listening(138, 'udp4'))
    results.append(action_utils.diagnose_port_listening(139, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(139, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(445, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(445, 'tcp6'))

    return results
