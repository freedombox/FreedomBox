# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Shadowsocks Client."""

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
        _('Your {box_name} can run a Shadowsocks client, that can connect to '
          'a Shadowsocks server. It will also run a SOCKS5 proxy. Local '
          'devices can connect to this proxy, and their data will be '
          'encrypted and proxied through the Shadowsocks server.'),
        box_name=_(cfg.box_name)),
    _('To use Shadowsocks after setup, set the SOCKS5 proxy URL in your '
      'device, browser or application to http://freedombox_address:1080/')
]


class ShadowsocksApp(app_module.App):
    """FreedomBox app for Shadowsocks Client."""

    app_id = 'shadowsocks'

    _version = 3

    DAEMON = 'shadowsocks-libev-local@freedombox'

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Shadowsocks Client'),
                               icon_filename='shadowsocks',
                               description=_description,
                               manual_page='Shadowsocks', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-shadowsocks', info.name,
                              info.icon_filename, info.tags,
                              'shadowsocks:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-shadowsocks', info.name, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('shadowsocks:index'), tags=info.tags,
            login_required=True)
        self.add(shortcut)

        packages = Packages('packages-shadowsocks', ['shadowsocks-libev'])
        self.add(packages)

        firewall = Firewall('firewall-shadowsocks', info.name,
                            ports=['shadowsocks-local-plinth'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon('daemon-shadowsocks', self.DAEMON,
                        listen_ports=[(1080, 'tcp4'), (1080, 'tcp6')])
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-shadowsocks',
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
