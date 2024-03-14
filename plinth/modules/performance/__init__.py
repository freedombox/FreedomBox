# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for System Monitoring (cockpit-pcp) in ‘System’.
"""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages

from . import manifest

name = _('Performance')

_description = [
    _('Performance app allows you to collect, store and view information '
      'about utilization of the hardware. This can give you basic insights '
      'into usage patterns and whether the hardware is overloaded by users '
      'and services.'),
    _('Performance metrics are collected by Performance Co-Pilot and can be '
      'viewed using the Cockpit app.'),
]


class PerformanceApp(app_module.App):
    """FreedomBox app for Performance."""

    app_id = 'performance'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Performance'), icon='fa-bar-chart',
                               short_description=_('System Monitoring'),
                               description=_description,
                               manual_page='Performance',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-performance', info.name,
                              info.short_description, info.icon,
                              'performance:index',
                              parent_url_name='system:administration',
                              order=40)
        self.add(menu_item)

        packages = Packages('packages-performance', ['cockpit-pcp'])
        self.add(packages)

        backup_restore = BackupRestore('backup-restore-performance',
                                       **manifest.backup)
        self.add(backup_restore)

        daemon_0 = Daemon('daemon-performance-0', 'pmcd.service',
                          listen_ports=None)
        self.add(daemon_0)

        daemon_1 = Daemon('daemon-performance-1', 'pmie.service',
                          listen_ports=None)
        self.add(daemon_1)

        daemon_2 = Daemon('daemon-performance-2', 'pmlogger.service',
                          listen_ports=None)
        self.add(daemon_2)

        daemon_3 = Daemon('daemon-performance-3', 'pmproxy.service',
                          listen_ports=None)
        self.add(daemon_3)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()
