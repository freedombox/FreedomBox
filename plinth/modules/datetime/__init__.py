# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure system date and time.
"""

import subprocess

from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon, RelatedDaemon
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules.backups.components import BackupRestore
from plinth.package import Packages

from . import manifest

_description = [
    _('Network time server is a program that maintains the system time '
      'in synchronization with servers on the Internet.')
]


class DateTimeApp(app_module.App):
    """FreedomBox app for date and time if time syncronization is unmanaged."""

    app_id = 'datetime'

    _version = 2

    _time_managed = None

    @property
    def can_be_disabled(self):
        """Return whether the app can be disabled."""
        return self._is_time_managed()

    def _is_time_managed(self):
        """Check whether time should be syncronized by the systemd-timesyncd.

        systemd-timesyncd does not run if we have another NTP daemon installed
        or FreedomBox runs inside a container where the host manages the time.

        """
        if self._time_managed is None:
            try:
                # Replace with the command 'systemd-analyze condition
                # --unit=systemd-timesyncd.service' when --unit argument
                # becomes available in a newer systemd.
                process = subprocess.run(
                    ['systemd-detect-virt', '--container'], check=False,
                    stdout=subprocess.PIPE)
                self._time_managed = (
                    process.stdout.decode().strip() == 'none')
            except (FileNotFoundError, subprocess.CalledProcessError):
                # When systemd-timesyncd will not run.
                self._time_managed = False

        return self._time_managed

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Date & Time'),
                               icon='fa-clock-o', description=_description,
                               manual_page='DateTime')
        self.add(info)

        menu_item = menu.Menu('menu-datetime', info.name, None, info.icon,
                              'datetime:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-datetime', ['systemd-timesyncd'])
        self.add(packages)

        related_daemon = RelatedDaemon('daemon-datetime-timedated',
                                       'systemd-timedated')
        self.add(related_daemon)

        if self._is_time_managed():
            daemon = Daemon('daemon-datetime', 'systemd-timesyncd')
            self.add(daemon)

        backup_restore = BackupRestore('backup-restore-datetime',
                                       **manifest.backup)
        self.add(backup_restore)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()
        if self._is_time_managed():
            results.append(_diagnose_time_synchronized())

        return results

    def has_diagnostics(self):
        """Return that app has diagnostics only when time is managed."""
        return self._is_time_managed()

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()


def _diagnose_time_synchronized() -> DiagnosticCheck:
    """Check whether time is synchronized to NTP server."""
    result = Result.FAILED
    try:
        output = subprocess.check_output(
            ['timedatectl', 'show', '--property=NTPSynchronized', '--value'])
        if 'yes' in output.decode():
            result = Result.PASSED
    except subprocess.CalledProcessError:
        pass

    return DiagnosticCheck('datetime-ntp-sync',
                           gettext_noop('Time synchronized to NTP server'),
                           result)
