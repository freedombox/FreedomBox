# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Shadowsocks Server."""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('Shadowsocks is a tool for securely forwarding network requests to a'
      ' remote server. It consists of two parts: (1) a Shadowsocks server,'
      ' and (2) a Shadowsocks client with a SOCKS5 proxy.'),
    _('Shadowsocks can be used to bypass Internet filtering and '
      'censorship. This requires that the Shadowsocks server is in a '
      'location where it can freely access the Internet, without '
      'filtering.'),
    format_lazy(
        _('Your {box_name} can run a Shadowsocks server, that allows '
          'Shadowsocks clients to connect to it. Clients\' data will be '
          'encrypted and proxied through this server.'),
        box_name=_(cfg.box_name)),
]


class ShadowsocksServerApp(app_module.App):
    """FreedomBox app for Shadowsocks Server."""

    app_id = 'shadowsocksserver'

    _version = 1

    DAEMON = 'shadowsocks-libev-server@fbxserver'

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Shadowsocks Server'),
                               icon_filename='shadowsocks',
                               description=_description,
                               manual_page='Shadowsocks', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-shadowsocks-server', info.name,
                              info.icon_filename, info.tags,
                              'shadowsocksserver:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-shadowsocks-server', info.name, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('shadowsocksserver:index'),
            tags=info.tags, login_required=True)
        self.add(shortcut)

        packages = Packages('packages-shadowsocks-server',
                            ['shadowsocks-libev'])
        self.add(packages)

        firewall = Firewall('firewall-shadowsocks-server', info.name,
                            ports=['shadowsocks-server-freedombox'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon(
            'daemon-shadowsocks-server', self.DAEMON,
            listen_ports=[(8388, 'tcp4'), (8388, 'tcp6'), (8388, 'udp4'),
                          (8388, 'udp6')])
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-shadowsocks-server',
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
