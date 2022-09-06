# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Transmission server.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
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

    _version = 4

    DAEMON = 'transmission-daemon'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {
            'bit-torrent': _('Download files using BitTorrent applications')
        }

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Transmission'),
            icon_filename='transmission',
            short_description=_('BitTorrent Web Client'),
            description=_description, manual_page='Transmission',
            clients=manifest.clients,
            donation_url='https://transmissionbt.com/donate/')
        self.add(info)

        menu_item = menu.Menu('menu-transmission', info.name,
                              info.short_description, info.icon_filename,
                              'transmission:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-transmission', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            url='/transmission', clients=info.clients, login_required=True,
            allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-transmission', ['transmission-daemon'])
        self.add(packages)

        firewall = Firewall('firewall-transmission', info.name,
                            ports=['http', 'https',
                                   'transmission-client'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-transmission', 'transmission-plinth',
                              urls=['https://{host}/transmission'])
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

        if old_version and old_version <= 3 and self.is_enabled():
            self.get_component('firewall-transmission').enable()

        new_configuration = {
            'rpc-whitelist-enabled': False,
            'rpc-authentication-required': False
        }
        privileged.merge_configuration(new_configuration)
        add_user_to_share_group(SYSTEM_USER, TransmissionApp.DAEMON)
        self.enable()
