# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure BIND server."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages, install
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('BIND enables you to publish your Domain Name System (DNS) information '
      'on the Internet, and to resolve DNS queries for your user devices on '
      'your network.'),
    format_lazy(
        _('Currently, on {box_name}, BIND is only used to resolve DNS queries '
          'for other machines on local network. It is also incompatible with '
          'sharing Internet connection from {box_name}.'),
        box_name=_(cfg.box_name)),
]


class BindApp(app_module.App):
    """FreedomBox app for Bind."""

    app_id = 'bind'

    _version = 4

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('BIND'), icon='fa-globe-w',
                               short_description=_('Domain Name Server'),
                               description=_description, manual_page='Bind')
        self.add(info)

        menu_item = menu.Menu('menu-bind', info.name, info.short_description,
                              info.icon, 'bind:index',
                              parent_url_name='system:visibility', order=30)
        self.add(menu_item)

        packages = Packages('packages-bind', ['bind9'])
        self.add(packages)

        firewall = Firewall('firewall-bind', info.name, ports=['dns'],
                            is_external=False)
        self.add(firewall)

        daemon = Daemon(
            'daemon-bind', 'named', listen_ports=[(53, 'tcp6'), (53, 'udp6'),
                                                  (53, 'tcp4'), (53, 'udp4')])
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-bind',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup(old_version)
        if not old_version:
            self.enable()

    def force_upgrade(self, _packages):
        """Force upgrade the managed packages to resolve conffile prompt."""
        install(['bind9'], force_configuration='old')
        return True
