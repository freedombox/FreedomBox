# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Shaarli.
"""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('Shaarli allows you to save and share bookmarks.'),
    _('Note that Shaarli only supports a single user account, which you will '
      'need to setup on the initial visit.'),
]


class ShaarliApp(app_module.App):
    """FreedomBox app for Shaarli."""

    app_id = 'shaarli'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Shaarli'), icon_filename='shaarli',
                               short_description=_('Bookmarks'),
                               description=_description, manual_page='Shaarli',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-shaarli', info.name,
                              info.short_description, info.icon_filename,
                              'shaarli:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-shaarli', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/shaarli',
                                      clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        packages = Packages('packages-shaarli', ['shaarli'])
        self.add(packages)

        firewall = Firewall('firewall-shaarli', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-shaarli', 'shaarli')
        self.add(webserver)

        backup_restore = BackupRestore('backup-restore-shaarli',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()
