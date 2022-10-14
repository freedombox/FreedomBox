# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Shadowsocks."""

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
    _('Shadowsocks is a lightweight and secure SOCKS5 proxy, designed to '
      'protect your Internet traffic. It can be used to bypass Internet '
      'filtering and censorship.'),
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
    """FreedomBox app for Shadowsocks."""

    app_id = 'shadowsocks'

    _version = 3

    DAEMON = 'shadowsocks-libev-local@freedombox'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Shadowsocks'),
                               icon_filename='shadowsocks',
                               short_description=_('Socks5 Proxy'),
                               description=_description,
                               manual_page='Shadowsocks')
        self.add(info)

        menu_item = menu.Menu('menu-shadowsocks', info.name,
                              info.short_description, info.icon_filename,
                              'shadowsocks:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-shadowsocks', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('shadowsocks:index'),
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
        self.enable()
