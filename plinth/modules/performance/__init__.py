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

version = 1

name = _('Performance')

managed_services = [
    'pmcd.service', 'pmie.service', 'pmlogger.service', 'pmproxy.service'
]

managed_packages = ['cockpit-pcp']

_description = [
    _('Performance app allows you to collect, store and view information '
      'about utilization of the hardware. This can give you basic insights '
      'into usage patterns and whether the hardware is overloaded by users '
      'and services.'),
    _('Performance metrics are collected by Performance Co-Pilot and can be '
      'viewed using the Cockpit app.'),
]

app = None


class PerformanceApp(app_module.App):
    """FreedomBox app for Performance."""

    app_id = 'performance'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Performance'), icon='fa-bar-chart',
                               short_description=_('System Monitoring'),
                               description=_description,
                               manual_page='Performance',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-performance', info.name,
                              info.short_description, info.icon,
                              'performance:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-performance', managed_packages)
        self.add(packages)

        backup_restore = BackupRestore('backup-restore-performance',
                                       **manifest.backup)
        self.add(backup_restore)

        daemon_0 = Daemon('daemon-performance-0', managed_services[0],
                          listen_ports=None)
        self.add(daemon_0)

        daemon_1 = Daemon('daemon-performance-1', managed_services[1],
                          listen_ports=None)
        self.add(daemon_1)

        daemon_2 = Daemon('daemon-performance-2', managed_services[2],
                          listen_ports=None)
        self.add(daemon_2)

        daemon_3 = Daemon('daemon-performance-3', managed_services[3],
                          listen_ports=None)
        self.add(daemon_3)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
