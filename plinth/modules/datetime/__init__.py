# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure system date and time.
"""

import subprocess

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 2

is_essential = True

managed_services = ['systemd-timesyncd']

managed_packages = []

_description = [
    _('Network time server is a program that maintains the system time '
      'in synchronization with servers on the Internet.')
]

app = None


class DateTimeApp(app_module.App):
    """FreedomBox app for date and time if time syncronization is unmanaged."""

    app_id = 'datetime'

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
                output = subprocess.check_output([
                    'systemctl', 'show', '--property=ConditionResult',
                    '--value', 'systemd-timesyncd'
                ])
                self._time_managed = 'yes' in output.decode()
            except subprocess.CalledProcessError:
                # When systemd is not running.
                self._time_managed = False

        return self._time_managed

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential,
                               name=_('Date & Time'), icon='fa-clock-o',
                               description=_description,
                               manual_page='DateTime')
        self.add(info)

        menu_item = menu.Menu('menu-datetime', info.name, None, info.icon,
                              'datetime:index', parent_url_name='system')
        self.add(menu_item)

        if self._is_time_managed():
            daemon = Daemon('daemon-datetime', managed_services[0])
            self.add(daemon)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(_diagnose_time_synchronized())
        return results


def init():
    """Initialize the date/time module."""
    global app
    app = DateTimeApp()

    if app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('post', app.enable)


def _diagnose_time_synchronized():
    """Check whether time is synchronized to NTP server."""
    result = 'failed'
    try:
        output = subprocess.check_output(
            ['timedatectl', 'show', '--property=NTPSynchronized', '--value'])
        if 'yes' in output.decode():
            result = 'passed'
    except subprocess.CalledProcessError:
        pass

    return [_('Time synchronized to NTP server'), result]
