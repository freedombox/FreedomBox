# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Transmission server.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.modules.users import add_user_to_share_group
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('Transmission is a BitTorrent client with a web interface.'),
    _('BitTorrent is a peer-to-peer file sharing protocol. '
      'Note that BitTorrent is not anonymous.'),
    _('Please do not change the default port of the Transmission daemon.'),
    format_lazy(
        _('Compared to <a href="{deluge_url}">'
          'Deluge</a>, Transmission is simpler and lightweight but is less '
          'customizable.'), deluge_url=reverse_lazy('deluge:index')),
    format_lazy(
        _('It can be accessed by <a href="{users_url}">any user</a> on '
          '{box_name} belonging to the bit-torrent group.'),
        box_name=_(cfg.box_name), users_url=reverse_lazy('users:index')),
    format_lazy(
        _('In addition to the web interface, mobile and desktop apps can also '
          'be used to remotely control Transmission on {box_name}. To '
          'configure remote control apps, use the URL '
          '<a href="/transmission-remote/rpc">/transmission-remote/rpc</a>.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('<a href="{samba_url}">Samba</a> shares can be set as the '
          'default download directory from the dropdown menu below.'),
        samba_url=reverse_lazy('samba:index')),
    format_lazy(
        _('After a download has completed, you can also access your files '
          'using the <a href="{sharing_url}">Sharing</a> app.'),
        sharing_url=reverse_lazy('sharing:index'))
]

SYSTEM_USER = 'debian-transmission'


class TransmissionApp(app_module.App):
    """FreedomBox app for Transmission."""

    app_id = 'transmission'

    _version = 8

    DAEMON = 'transmission-daemon'

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        groups = {
            'bit-torrent': _('Download files using BitTorrent applications')
        }

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Transmission'),
            icon_filename='transmission', description=_description,
            manual_page='Transmission', clients=manifest.clients,
            donation_url='https://transmissionbt.com/donate/',
            tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-transmission', info.name,
                              info.icon_filename, info.tags,
                              'transmission:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-transmission', info.name,
                                      icon=info.icon_filename,
                                      url='/transmission',
                                      clients=info.clients, tags=info.tags,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-transmission', ['transmission-daemon'],
                            rerun_setup_on_upgrade=True)
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-transmission', [
            '/etc/apache2/conf-available/transmission-plinth.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-transmission', info.name,
                            ports=['http', 'https',
                                   'transmission-client'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-transmission', ['9091'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-transmission', 'transmission-plinth',
                              urls=['https://{host}/transmission'],
                              last_updated_version=8)
        self.add(webserver)

        daemon = Daemon(
            'daemon-transmission', self.DAEMON, listen_ports=[
                (9091, 'tcp4'),
                (51413, 'tcp4'),
                (51413, 'tcp6'),
                (51413, 'udp4'),
            ])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-transmission',
                                          reserved_usernames=[SYSTEM_USER],
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-transmission',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)

        new_configuration = {
            'rpc-whitelist-enabled': False,
            'rpc_whitelist_enabled': False,
            'rpc-authentication-required': False,
            'rpc_authentication_required': False,
        }

        if old_version:
            download_dir = get_download_dir()
            new_configuration['download-dir'] = download_dir
            new_configuration['download_dir'] = download_dir

        privileged.merge_configuration(new_configuration)
        add_user_to_share_group(SYSTEM_USER, TransmissionApp.DAEMON)

        if not old_version:
            self.enable()


def get_download_dir() -> str:
    """Return the configured download directory."""
    configuration = privileged.get_configuration()
    old = configuration.get('download-dir')  # Trixie and older
    if old:
        return old

    return configuration.get('download_dir')  # Forky and newer
