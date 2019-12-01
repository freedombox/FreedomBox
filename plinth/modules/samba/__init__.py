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

import json
import socket

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.users import create_group
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_services = ['smbd', 'nmbd']

managed_packages = ['samba', 'acl']

name = _('Samba')

short_description = _('File Sharing')

description = [
    _('Samba allows to share files and folders between FreedomBox and '
      'other computers in your local network.'),
    format_lazy(
        _('After installation, you can choose which disks to use for sharing. '
          'Enabled {hostname} shares are open to everyone in your local '
          'network and are accessible under Network section in the file '
          'manager on your computer.'), hostname=socket.gethostname().upper())
]

group = ('freedombox-share', _('Access shared folders from inside the server'))

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

        daemon_nmbd = Daemon('daemon-samba-nmbd', managed_services[1])
        self.add(daemon_nmbd)


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
    create_group('freedombox-share')
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


def add_share(mount_point, filesystem):
    """Add a share."""
    command = ['add-share', '--mount-point', mount_point]
    if filesystem in ['ntfs', 'vfat']:
        command = command + ['--windows-filesystem']
    actions.superuser_run('samba', command)


def delete_share(mount_point):
    """Delete a share."""
    command = ['delete-share', '--mount-point', mount_point]
    actions.superuser_run('samba', command)


def get_shares():
    """Get defined shares."""
    output = actions.superuser_run('samba', ['get-shares'])

    return json.loads(output)


def backup_pre(packet):
    """Save registry share configuration."""
    actions.superuser_run('samba', ['dump-shares'])


def restore_post(packet):
    """Restore configuration."""
    actions.superuser_run('samba', ['setup'])
    actions.superuser_run('samba', ['restore-shares'])
