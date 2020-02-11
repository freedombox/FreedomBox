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

import pathlib
import re
import subprocess

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

managed_services = ['ssh']

managed_packages = ['openssh-server']

_description = [
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
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential,
                               name=_('Secure Shell (SSH) Server'),
                               icon='fa-terminal', description=_description)
        self.add(info)

        menu_item = menu.Menu('menu-ssh', info.name, None, info.icon,
                              'ssh:index', parent_url_name='system')
        self.add(menu_item)

        firewall = Firewall('firewall-ssh', info.name, ports=['ssh'],
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


def get_host_keys():
    """Return Host keys of the system."""
    etc_ssh = pathlib.Path('/etc/ssh/')
    host_keys = []
    pattern = re.compile(r'^(?P<bit_size>\d+) (?P<fingerprint>[\S]+) '
                         r'.+ \((?P<algorithm>\w+)\)$')

    for public_key in etc_ssh.glob('*.pub'):
        process = subprocess.run(['ssh-keygen', '-l', '-f',
                                  str(public_key)], stdout=subprocess.PIPE,
                                 check=True)
        output = process.stdout.decode().strip()
        if output:
            match = re.match(pattern, output)
            if match:
                host_keys.append(match.groupdict())

    return host_keys


def is_password_authentication_disabled():
    """Return if ssh password authentication is enabled."""
    return actions.superuser_run('ssh',
                                 ['get-password-config']).strip() == 'no'
