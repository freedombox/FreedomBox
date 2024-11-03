# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure RSS-Bridge.
"""
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('RSS-Bridge generates RSS and Atom feeds for websites that do not have '
      'one. Generated feeds can be consumed by any feed reader.'),
    format_lazy(
        _('When enabled, RSS-Bridge can be accessed by <a href="{users_url}">'
          'any user</a> belonging to the feed-reader group.'),
        users_url=reverse_lazy('users:index')),
    format_lazy(
        _('You can use RSS-Bridge with <a href="{ttrss_url}">Tiny Tiny '
          'RSS</a> to follow various websites. When adding a feed, enable '
          'authentication and use your {box_name} credentials.'),
        ttrss_url=reverse_lazy('ttrss:index'), box_name=_(cfg.box_name)),
]


class RSSBridgeApp(app_module.App):
    """FreedomBox app for RSS-Bridge."""

    app_id = 'rssbridge'

    _version = 2

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        groups = {'feed-reader': _('Read and subscribe to news feeds')}

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('RSS-Bridge'), icon_filename='rssbridge',
                               short_description=_('RSS Feed Generator'),
                               description=_description,
                               manual_page='RSSBridge', donation_url=None,
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-rssbridge', info.name,
                              info.short_description, info.icon_filename,
                              'rssbridge:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-rssbridge', name=info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/rss-bridge/', login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-rssbridge', ['rss-bridge'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-rssbridge', [
            '/etc/apache2/conf-available/rss-bridge.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-rssbridge', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-rssbridge', 'rss-bridge',
                              urls=['https://{host}/rss-bridge/'])
        self.add(webserver)

        users_and_groups = UsersAndGroups('users-and-groups-rssbridge',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-rssbridge',
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
