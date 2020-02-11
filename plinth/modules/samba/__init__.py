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

import grp
import json
import os
import pwd
import socket

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['smbd', 'nmbd']

managed_packages = ['samba', 'acl']

_description = [
    _('Samba allows to share files and folders between FreedomBox and '
      'other computers in your local network.'),
    format_lazy(
        _('After installation, you can choose which disks to use for sharing. '
          'Enabled shares are accessible in the file manager on your computer '
          'at location \\\\{hostname} (on Windows) or smb://{hostname}.local '
          '(on Linux and Mac). There are three types of shares '
          'you can choose from: '), hostname=socket.gethostname()),
    _('Open share - accessible to everyone in your local network.'),
    _('Group share - accessible only to FreedomBox users who are in the '
      'freedombox-share group.'),
    _('Home share - every user in the freedombox-share group can have their '
      'own private space.'),
]

group = ('freedombox-share', _('Access to the private shares'))

app = None


class SambaApp(app_module.App):
    """FreedomBox app for Samba file sharing."""

    app_id = 'samba'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Samba'), icon_filename='samba',
                               short_description=_('File Sharing'),
                               description=_description, clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-samba', info.name, info.short_description,
                              info.icon_filename, 'samba:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-samba', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('samba:index'), clients=info.clients,
            login_required=True, allowed_groups=[group[0]])
        self.add(shortcut)

        firewall = Firewall('firewall-samba', info.name, ports=['samba'])
        self.add(firewall)

        daemon = Daemon(
            'daemon-samba', managed_services[0], listen_ports=[(139, 'tcp4'),
                                                               (139, 'tcp6'),
                                                               (445, 'tcp4'),
                                                               (445, 'tcp6')])
        self.add(daemon)

        daemon_nmbd = Daemon('daemon-samba-nmbd', managed_services[1],
                             listen_ports=[(137, 'udp4'), (138, 'udp4')])

        self.add(daemon_nmbd)


def init():
    """Initialize the module."""
    global app
    app = SambaApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'samba', ['setup'])
    helper.call('post', app.enable)


def add_share(mount_point, share_type, filesystem):
    """Add a share."""
    command = [
        'add-share', '--mount-point', mount_point, '--share-type', share_type
    ]
    if filesystem in ['ntfs', 'vfat']:
        command = command + ['--windows-filesystem']
    actions.superuser_run('samba', command)


def delete_share(mount_point, share_type):
    """Delete a share."""
    actions.superuser_run('samba', [
        'delete-share', '--mount-point', mount_point, '--share-type',
        share_type
    ])


def get_users():
    """Get non-system users who are in the freedombox-share or admin group."""
    output = actions.superuser_run('samba', ['get-users'])
    samba_users = json.loads(output)['users']
    group_users = grp.getgrnam('freedombox-share').gr_mem + grp.getgrnam(
        'admin').gr_mem

    allowed_users = []
    for group_user in group_users:
        uid = pwd.getpwnam(group_user).pw_uid
        if uid > 1000:
            allowed_users.append(group_user)

    return {
        'access_ok':
            sorted(set(allowed_users) & set(samba_users)),
        'password_re_enter_needed':
            sorted(set(allowed_users) - set(samba_users))
    }


def get_shares():
    """Get defined shares."""
    output = actions.superuser_run('samba', ['get-shares'])

    return json.loads(output)


def disk_name(mount_point):
    """Get a disk name."""
    share_name = os.path.basename(mount_point)
    if not share_name:
        share_name = 'disk'

    return share_name


def backup_pre(packet):
    """Save registry share configuration."""
    actions.superuser_run('samba', ['dump-shares'])


def restore_post(packet):
    """Restore configuration."""
    actions.superuser_run('samba', ['setup'])
    actions.superuser_run('samba', ['restore-shares'])
