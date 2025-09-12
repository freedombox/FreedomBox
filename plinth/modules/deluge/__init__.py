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
from plinth.modules.upgrades.utils import get_current_release
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


class DelugePackages(Packages):
    """Mark deluge app as not available in Debian Bookworm.

    deluge-web is broken in Debian Bookworm. Related bug report:
    https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1031593
    """

    def is_available(self) -> bool:
        if get_current_release()[1] == 'bookworm':
            return False

        return super().is_available()


class DelugeApp(app_module.App):
    """FreedomBox app for Deluge."""

    app_id = 'deluge'

    _version = 9

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        groups = {
            'bit-torrent': _('Download files using BitTorrent applications')
        }

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Deluge'),
            icon_filename='deluge', description=_description,
            manual_page='Deluge', clients=manifest.clients,
            donation_url='https://www.patreon.com/deluge_cas',
            tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-deluge', info.name, info.icon_filename,
                              info.tags, 'deluge:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-deluge', info.name,
                                      url='/deluge', icon=info.icon_filename,
                                      clients=info.clients, tags=info.tags,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = DelugePackages('packages-deluge', ['deluged', 'deluge-web'])
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
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()
