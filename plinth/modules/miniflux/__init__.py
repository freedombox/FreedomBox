# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for Miniflux."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon, SharedDaemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('Miniflux is a web-based tool that aggregates news and blog updates from'
      ' various websites into one centralized, easy-to-read format. It has a '
      'simple interface and focuses on a distraction-free reading experience. '
      'You can can subscribe to your favorite sites and access full article '
      'contents within the reader itself.'),
    _('Key features include keyboard shortcuts for quick navigation, full-text'
      ' search, filtering articles, categories and favorites. Miniflux '
      'preserves user privacy by removing trackers. The primary interface is '
      'web-based. There are several third-party '
      '<a href="https://miniflux.app/docs/apps.html">clients</a> as well.'),
]


class MinifluxApp(app_module.App):
    """FreedomBox app for Miniflux."""

    app_id = 'miniflux'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(self.app_id, self._version, name=_('Miniflux'),
                               icon_filename='miniflux',
                               description=_description,
                               manual_page='miniflux',
                               clients=manifest.clients, tags=manifest.tags,
                               donation_url='https://miniflux.app/#donations')
        self.add(info)

        menu_item = menu.Menu('menu-miniflux', info.name, info.icon_filename,
                              info.tags, 'miniflux:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-miniflux', info.name,
                                      info.icon_filename, url='/miniflux',
                                      clients=manifest.clients, tags=info.tags,
                                      login_required=True)
        self.add(shortcut)

        # miniflux package does not depend on postgres. Install postgresql,
        # start it and only then install miniflux.
        packages = Packages('packages-miniflux-postgresql', ['postgresql'])
        self.add(packages)

        packages = Packages('packages-miniflux', ['miniflux'])
        self.add(packages)

        drop_in_configs = DropinConfigs(
            'dropin-configs-miniflux',
            ['/etc/apache2/conf-available/miniflux-freedombox.conf'])
        self.add(drop_in_configs)

        firewall = Firewall('firewall-miniflux', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-miniflux', 'miniflux-freedombox',
                              urls=['https://{host}/miniflux/'])
        self.add(webserver)

        daemon = SharedDaemon('shared-daemon-miniflux-postgresql',
                              'postgresql')
        self.add(daemon)

        daemon = Daemon('daemon-miniflux', 'miniflux',
                        listen_ports=[(8788, 'tcp4'), (8788, 'tcp6')])
        self.add(daemon)

        backup_restore = MinifluxBackupRestore('backup-restore-miniflux',
                                               **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version=None):
        """Install and configure the app."""
        privileged.pre_setup()

        # Database needs to be running for successful initialization or upgrade
        # of miniflux database. 1. The app and database are being freshly
        # installed. 2. The app is being freshly installed, but database server
        # is already installed but disabled. 3. The app is being updated to new
        # version but is currently disabled (DB is installed but disabled or
        # enabled).
        with self.get_component(
                'shared-daemon-miniflux-postgresql').ensure_running():
            super().setup(old_version)

        privileged.setup(old_version)
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        privileged.uninstall()
        with self.get_component(
                'shared-daemon-miniflux-postgresql').ensure_running():
            # Database needs to be running for successful removal miniflux
            # database.
            super().uninstall()


class MinifluxBackupRestore(BackupRestore):
    """Component to backup/restore Miniflux."""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        privileged.dump_database()

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        privileged.restore_database()
