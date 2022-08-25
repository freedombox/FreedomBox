# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure OpenVPN server."""

import os

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    format_lazy(
        _('Virtual Private Network (VPN) is a technique for securely '
          'connecting two devices in order to access resources of a '
          'private network.  While you are away from home, you can connect '
          'to your {box_name} in order to join your home network and '
          'access private/internal services provided by {box_name}. '
          'You can also access the rest of the Internet via {box_name} '
          'for added security and anonymity.'), box_name=_(cfg.box_name))
]

SERVER_CONFIGURATION_FILE = '/etc/openvpn/server/freedombox.conf'


class OpenVPNApp(app_module.App):
    """FreedomBox app for OpenVPN."""

    app_id = 'openvpn'

    _version = 4

    @property
    def can_be_disabled(self):
        """Return whether the app can be disabled."""
        return privileged.is_setup()

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        self.groups = {'vpn': _('Connect to VPN services')}

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('OpenVPN'), icon_filename='openvpn',
                               short_description=_('Virtual Private Network'),
                               description=_description, manual_page='OpenVPN',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-openvpn', info.name,
                              info.short_description, info.icon_filename,
                              'openvpn:index', parent_url_name='apps')
        self.add(menu_item)

        download_profile = \
            format_lazy(_('<a class="btn btn-primary btn-sm" href="{link}">'
                          'Download Profile</a>'),
                        link=reverse_lazy('openvpn:profile'))
        shortcut = frontpage.Shortcut(
            'shortcut-openvpn', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description + [download_profile],
            manual_page=info.manual_page,
            configure_url=reverse_lazy('openvpn:index'), login_required=True,
            allowed_groups=['vpn'])
        self.add(shortcut)

        packages = Packages('packages-openvpn', ['openvpn', 'easy-rsa'])
        self.add(packages)

        firewall = Firewall('firewall-openvpn', info.name, ports=['openvpn'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-openvpn', 'openvpn-server@freedombox',
                        listen_ports=[(1194, 'udp4'), (1194, 'udp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-openvpn',
                                          groups=self.groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-openvpn',
                                       **manifest.backup)
        self.add(backup_restore)

    def is_enabled(self):
        """Return whether all the leader components are enabled.

        Return True when there are no leader components and OpenVPN setup
        is done.
        """
        return super().is_enabled() and privileged.is_setup()

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        self.enable()


def is_using_ecc():
    """Return whether the service is using ECC."""
    if os.path.exists(SERVER_CONFIGURATION_FILE):
        with open(SERVER_CONFIGURATION_FILE, 'r',
                  encoding='utf-8') as file_handle:
            for line in file_handle:
                if line.strip() == 'dh none':
                    return True
    return False
