# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure samba."""

import grp
import pwd
import socket

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

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


class SambaApp(app_module.App):
    """FreedomBox app for Samba file sharing."""

    app_id = 'samba'

    _version = 5

    def __init__(self) -> None:
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

        users_and_groups = UsersAndGroups('users-and-groups-samba',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = SambaBackupRestore('backup-restore-samba',
                                            **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


class SambaBackupRestore(BackupRestore):
    """Component to backup/restore Samba."""

    def backup_pre(self, packet):
        """Save registry share configuration."""
        super().backup_pre(packet)
        privileged.dump_shares()

    def restore_post(self, packet):
        """Restore configuration."""
        super().restore_post(packet)
        privileged.setup()
        privileged.restore_shares()


def add_share(mount_point, share_type, filesystem):
    """Add a share."""
    windows_filesystem = (filesystem in ['ntfs', 'vfat'])
    privileged.add_share(mount_point, share_type, windows_filesystem)


def get_users():
    """Get non-system users who are in the freedombox-share or admin group."""
    samba_users = privileged.get_users()
    group_users = grp.getgrnam('freedombox-share').gr_mem + grp.getgrnam(
        'admin').gr_mem

    allowed_users = []
    for group_user in group_users:
        try:
            uid = pwd.getpwnam(group_user).pw_uid
        except KeyError:  # User doesn't exist
            continue

        if uid > 1000:
            allowed_users.append(group_user)

    return {
        'access_ok':
            sorted(set(allowed_users) & set(samba_users)),
        'password_re_enter_needed':
            sorted(set(allowed_users) - set(samba_users))
    }
