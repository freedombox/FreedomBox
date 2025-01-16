# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for OpenSSH server."""

import pathlib
import re
import subprocess

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('A Secure Shell server uses the secure shell protocol to accept '
      'connections from remote computers. An authorized remote computer '
      'can perform administration tasks, copy files or run other services '
      'using such connections.')
]


class SSHApp(app_module.App):
    """FreedomBox app for SSH."""

    app_id = 'ssh'

    _version = 4

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               name=_('Secure Shell Server'),
                               icon='fa-terminal', description=_description,
                               manual_page='SecureShell', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-ssh', info.name, info.icon, info.tags,
                              'ssh:index',
                              parent_url_name='system:administration',
                              order=10)
        self.add(menu_item)

        packages = Packages('packages-ssh', ['openssh-server'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-ssh', [
            '/etc/fail2ban/jail.d/ssh-freedombox.conf',
        ])
        self.add(dropin_configs)

        dropin_configs = DropinConfigs('dropin-config-ssh-avahi', [
            '/etc/avahi/services/sftp-ssh.service',
            '/etc/avahi/services/ssh.service',
        ], copy_only=True)
        self.add(dropin_configs)

        firewall = Firewall('firewall-ssh', info.name, ports=['ssh'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-ssh', 'ssh')
        self.add(daemon)

        groups = {
            'freedombox-ssh': _('Remotely login using Secure Shell (SSH)')
        }
        users_and_groups = UsersAndGroups('users-and-groups-ssh',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-ssh', **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()
        elif old_version == 2 and privileged.are_users_restricted():
            privileged.restrict_users(True)
        elif old_version == 1:
            privileged.restrict_users(True)


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
