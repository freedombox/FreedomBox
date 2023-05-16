# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure a Deluge web client."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.modules.users import add_user_to_share_group
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('Deluge is a BitTorrent client that features a Web UI.'),
    _('The default password is \'deluge\', but you should log in and '
      'change it immediately after enabling this service.')
]

SYSTEM_USER = 'debian-deluged'


class DelugeApp(app_module.App):
    """FreedomBox app for Deluge."""

    app_id = 'deluge'

    _version = 8

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {
            'bit-torrent': _('Download files using BitTorrent applications')
        }

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Deluge'),
            icon_filename='deluge',
            short_description=_('BitTorrent Web Client'),
            description=_description, manual_page='Deluge',
            clients=manifest.clients,
            donation_url='https://www.patreon.com/deluge_cas')
        self.add(info)

        menu_item = menu.Menu('menu-deluge', info.name, info.short_description,
                              info.icon_filename, 'deluge:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-deluge', info.name,
                                      short_description=info.short_description,
                                      url='/deluge', icon=info.icon_filename,
                                      clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-deluge', ['deluged', 'deluge-web'])
        self.add(packages)

        dropin_configs = DropinConfigs(
            'dropin-configs-deluge',
            ['/etc/apache2/conf-available/deluge-plinth.conf'])
        self.add(dropin_configs)

        firewall = Firewall('firewall-deluge', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-deluge', ['8112'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-deluge', 'deluge-plinth',
                              urls=['https://{host}/deluge'])
        self.add(webserver)

        daemon = Daemon('daemon-deluged', 'deluged',
                        listen_ports=[(58846, 'tcp4')])
        self.add(daemon)

        daemon_web = Daemon('daemon-deluge-web', 'deluge-web',
                            listen_ports=[(8112, 'tcp4')])
        self.add(daemon_web)

        users_and_groups = UsersAndGroups('users-and-groups-deluge',
                                          reserved_usernames=[SYSTEM_USER],
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-deluge',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        add_user_to_share_group(SYSTEM_USER)
        privileged.setup()
        self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()
