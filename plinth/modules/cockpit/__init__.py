# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Cockpit.
"""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    format_lazy(
        _('Cockpit is a server manager that makes it easy to administer '
          'GNU/Linux servers via a web browser. On a {box_name}, controls '
          'are available for many advanced functions that are not usually '
          'required. A web based terminal for console operations is also '
          'available.'), box_name=_(cfg.box_name)),
    format_lazy(
        _('Cockpit can be used to perform advanced storage operations such as '
          'disk partitioning and RAID management. It can also be used for '
          'opening custom firewall ports and advanced networking such as '
          'bonding, bridging and VLAN management.')),
    format_lazy(
        _('It can be accessed by <a href="{users_url}">any user</a> on '
          '{box_name} belonging to the admin group.'),
        box_name=_(cfg.box_name), users_url=reverse_lazy('users:index')),
]


class CockpitApp(app_module.App):
    """FreedomBox app for Cockpit."""

    app_id = 'cockpit'

    _version = 3

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               depends=['apache'], is_essential=True,
                               name=_('Cockpit'), icon='fa-wrench',
                               icon_filename='cockpit',
                               short_description=_('Server Administration'),
                               description=_description, manual_page='Cockpit',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-cockpit', info.name,
                              info.short_description, info.icon,
                              'cockpit:index', parent_url_name='system')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-cockpit', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/_cockpit/', clients=info.clients,
                                      login_required=True,
                                      allowed_groups=['admin'])
        self.add(shortcut)

        packages = Packages('packages-cockpit', ['cockpit'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-cockpit', [
            '/etc/apache2/conf-available/cockpit-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-cockpit', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-cockpit', 'cockpit-freedombox',
                              urls=['https://{host}/_cockpit/'])
        self.add(webserver)

        daemon = Daemon('daemon-cockpit', 'cockpit.socket')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-cockpit',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()
