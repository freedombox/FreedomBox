# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure sharing."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    format_lazy(
        _('Sharing allows you to share files and folders on your {box_name} '
          'over the web with chosen groups of users.'),
        box_name=_(cfg.box_name))
]


class SharingApp(app_module.App):
    """FreedomBox app for sharing files."""

    app_id = 'sharing'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Sharing'), icon_filename='sharing',
                               manual_page='Sharing', description=_description)
        self.add(info)

        menu_item = menu.Menu('menu-sharing', info.name, None,
                              info.icon_filename, 'sharing:index',
                              parent_url_name='apps')
        self.add(menu_item)

        webserver = Webserver('webserver-sharing', 'sharing-freedombox')
        self.add(webserver)

        backup_restore = BackupRestore('backup-restore-sharing',
                                       **manifest.backup)
        self.add(backup_restore)

    def has_diagnostics(self):
        """Disable diagnostics button despite having webserver component."""
        return False

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        self.enable()
