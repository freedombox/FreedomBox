# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure GNOME desktop."""

from django.utils.translation import gettext_lazy as _

from plinth import action_utils
from plinth import app as app_module
from plinth import cfg, menu
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages
from plinth.privileged import service as service_privileged
from plinth.utils import format_lazy

from . import manifest

_description = [
    _('GNOME is a desktop environment that focuses on simplicity and ease of '
      'use.'),
    format_lazy(
        _('This app turns your {box_name} into a desktop computer if you '
          'physically connect a monitor, a keyboard, and a mouse to it. A '
          'browser, an office suite, and other basic utilities are available. '
          'You may install further graphical applications using the software '
          'center provided within.'), box_name=_(cfg.box_name)),
    _('This app is not suitable for low-end hardware. It requires at least '
      '4GiB for RAM, 4GiB or disk space and a GPU capable of basic 3D '
      'acceleration.'),
]


class GNOMEApp(app_module.App):
    """FreedomBox app for GNOME desktop."""

    app_id = 'gnome'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('GNOME'), icon_filename='gnome',
                               description=_description, manual_page='GNOME',
                               donation_url='https://www.gnome.org/donate/',
                               tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-gnome', info.name, info.icon_filename,
                              info.tags, 'gnome:index', parent_url_name='apps')
        self.add(menu_item)

        packages = Packages('packages-gnome', ['gnome'])
        self.add(packages)

        system_target = SystemTarget('system-target-gnome', 'graphical.target')
        self.add(system_target)

        backup_restore = BackupRestore('backup-restore-gnome',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()


class SystemTarget(app_module.LeaderComponent):
    """Component to set the default target systemd will boot into."""

    _DEFAULT_TARGET: str = 'multi-user.target'

    def __init__(self, component_id: str, target: str):
        """Initialize the component."""
        super().__init__(component_id)
        self.target = target

    def is_enabled(self) -> bool:
        """Return whether the component is enabled."""
        return action_utils.systemd_get_default() == self.target

    def enable(self) -> None:
        """Run operations to enable the component."""
        service_privileged.systemd_set_default(self.target)

    def disable(self) -> None:
        """Run operations to disable the component."""
        service_privileged.systemd_set_default(self._DEFAULT_TARGET)
