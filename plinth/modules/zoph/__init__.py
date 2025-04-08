# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Zoph web application."""

import logging

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import SharedDaemon
from plinth.modules.apache import privileged as apache_privileged
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

logger = logging.getLogger(__name__)

_description = [
    format_lazy(
        _('Zoph manages your photo collection. Photos are stored on your '
          '{box_name}, under your control. Instead of focusing on galleries '
          'for public display, Zoph focuses on managing them for your own '
          'use, organizing them by who took them, where they were taken, '
          'and who is in them. Photos can be linked to multiple hierarchical '
          'albums and categories. It is easy to find all photos containing a '
          'person, or photos taken on a date, or photos taken at a location '
          'using search, map and calendar views. Individual photos can be '
          'shared with others by sending a direct link.'),
        box_name=_(cfg.box_name)),
    format_lazy(
        _('The {box_name} user who setup Zoph will also become the '
          'administrator in Zoph. For additional users, accounts must be '
          'created both in {box_name} and in Zoph with the same user name.'),
        box_name=_(cfg.box_name))
]


class ZophApp(app_module.App):
    """FreedomBox app for Zoph."""

    app_id = 'zoph'

    _version = 3

    configure_when_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Zoph'), icon_filename='zoph',
                               description=_description, manual_page='Zoph',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-zoph', info.name, info.icon_filename,
                              info.tags, 'zoph:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-zoph', info.name,
                                      icon=info.icon_filename, url='/zoph/',
                                      clients=info.clients, tags=info.tags,
                                      login_required=True)
        self.add(shortcut)

        packages = Packages('packages-zoph', ['zoph', 'default-mysql-server'],
                            conflicts=['libpam-tmpdir'],
                            conflicts_action=Packages.ConflictsAction.REMOVE)
        self.add(packages)

        firewall = Firewall('firewall-zoph', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        dropin_configs = DropinConfigs('dropin-configs-zoph', [
            '/etc/apache2/conf-available/zoph-freedombox.conf',
        ])
        self.add(dropin_configs)

        webserver = Webserver('webserver-zoph', 'zoph',
                              urls=['https://{host}/zoph/'])
        self.add(webserver)

        webserver = Webserver('webserver-zoph-freedombox', 'zoph-freedombox')
        self.add(webserver)

        daemon = SharedDaemon('shared-daemon-zoph-mysql', 'mysql')
        self.add(daemon)

        backup_restore = ZophBackupRestore('backup-restore-zoph',
                                           **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        privileged.pre_install()
        with self.get_component('shared-daemon-zoph-mysql').ensure_running():
            # Database needs to be running for successful initialization or
            # upgrade of zoph database.
            super().setup(old_version)

        # Zoph brings mod-php as dependency and enables it. Re-run apache setup
        # to correct it. Disable mod-php, switch back to mpm-event, restart
        # apache2 if needed. Set old_version to an non-zero value so that
        # Snakeoil certificate is not regnerated.
        apache_privileged.setup(old_version=1)

        privileged.setup()
        if not old_version:
            self.enable()
        elif old_version < 2:
            if self.get_component('webserver-zoph').is_enabled():
                self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        # Before package uninstall, so that config file is still available
        privileged.uninstall()
        super().uninstall()


class ZophBackupRestore(BackupRestore):
    """Component to backup/restore Zoph database"""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        privileged.dump_database()

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        privileged.restore_database()
