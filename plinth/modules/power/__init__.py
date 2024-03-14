# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for power controls.
"""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.modules.backups.components import BackupRestore

from . import manifest

_description = [_('Restart or shut down the system.')]


class PowerApp(app_module.App):
    """FreedomBox app for power controls."""

    app_id = 'power'

    _version = 1

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Power'),
                               icon='fa-power-off', description=_description,
                               manual_page='Power')
        self.add(info)

        menu_item = menu.Menu('menu-power', info.name, None, info.icon,
                              'power:index',
                              parent_url_name='system:administration',
                              order=50)
        self.add(menu_item)

        backup_restore = BackupRestore('backup-restore-power',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()
