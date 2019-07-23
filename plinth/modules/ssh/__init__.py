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
FreedomBox app for OpenSSH server.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.views import AppView

from .manifest import backup

version = 1

is_essential = True

managed_services = ['ssh']

managed_packages = ['openssh-server']

name = _('Secure Shell (SSH) Server')

description = [
    _('A Secure Shell server uses the secure shell protocol to accept '
      'connections from remote computers. An authorized remote computer '
      'can perform administration tasks, copy files or run other services '
      'using such connections.')
]

port_forwarding_info = [('TCP', 22)]

app = None


class SSHApp(app_module.App):
    """FreedomBox app for SSH."""

    app_id = 'ssh'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-ssh', name, None, 'fa-terminal',
                              'ssh:index', parent_url_name='system')
        self.add(menu_item)

        firewall = Firewall('firewall-ssh', name, ports=['ssh'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-ssh', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the ssh module."""
    global app
    app = SSHApp()
    if app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Configure the module."""
    actions.superuser_run('ssh', ['setup'])


class SshAppView(AppView):
    app_id = 'ssh'
    name = name
    description = description
    port_forwarding_info = port_forwarding_info
