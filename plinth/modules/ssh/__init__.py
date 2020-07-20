# SPDX-License-Identifier: AGPL-3.0-or-later
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
