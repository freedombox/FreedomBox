# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure samba.
"""

import grp
import json
import pwd
import socket

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest

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

app = None


class SambaApp(app_module.App):
    """FreedomBox app for Samba file sharing."""

    app_id = 'samba'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'freedombox-share': _('Access to the private shares')}

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Samba'),
            icon_filename='samba', short_description=_('Network File Storage'),
            manual_page='Samba', description=_description,
            clients=manifest.clients,
            donation_url='https://www.samba.org/samba/donations.html')
        self.add(info)

        menu_item = menu.Menu('menu-samba', info.name, info.short_description,
                              info.icon_filename, 'samba:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-samba', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('samba:index'), clients=info.clients,
            login_required=True, allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-samba', ['samba', 'acl'])
        self.add(packages)

        firewall = Firewall('firewall-samba', info.name, ports=['samba'])
        self.add(firewall)

        daemon = Daemon(
            'daemon-samba', 'smbd', listen_ports=[(139, 'tcp4'), (139, 'tcp6'),
                                                  (445, 'tcp4'),
                                                  (445, 'tcp6')])
        self.add(daemon)

        daemon_nmbd = Daemon('daemon-samba-nmbd', 'nmbd',
                             listen_ports=[(137, 'udp4'), (138, 'udp4')])

        self.add(daemon_nmbd)

        users_and_groups = UsersAndGroups('users-and-groups-samba',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = SambaBackupRestore('backup-restore-samba',
                                            **manifest.backup)
        self.add(backup_restore)


class SambaBackupRestore(BackupRestore):
    """Component to backup/restore Samba."""

    def backup_pre(self, packet):
        """Save registry share configuration."""
        super().backup_pre(packet)
        actions.superuser_run('samba', ['dump-shares'])

    def restore_post(self, packet):
        """Restore configuration."""
        super().restore_post(packet)
        actions.superuser_run('samba', ['setup'])
        actions.superuser_run('samba', ['restore-shares'])


def setup(helper, old_version=None):
    """Install and configure the module."""
    app.setup(old_version)
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
