# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for OpenSSH server.
"""

import pathlib
import re
import subprocess

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages

from . import manifest

_description = [
    _('A Secure Shell server uses the secure shell protocol to accept '
      'connections from remote computers. An authorized remote computer '
      'can perform administration tasks, copy files or run other services '
      'using such connections.')
]


class SSHApp(app_module.App):
    """FreedomBox app for SSH."""

    app_id = 'ssh'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True,
                               name=_('Secure Shell (SSH) Server'),
                               icon='fa-terminal', description=_description,
                               manual_page='SecureShell')
        self.add(info)

        menu_item = menu.Menu('menu-ssh', info.name, None, info.icon,
                              'ssh:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-ssh', ['openssh-server'])
        self.add(packages)

        firewall = Firewall('firewall-ssh', info.name, ports=['ssh'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-ssh', 'ssh')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-ssh', **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        actions.superuser_run('ssh', ['setup'])
        self.enable()


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
