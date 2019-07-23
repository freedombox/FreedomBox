#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app to configure system date and time.
"""

import subprocess

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon

from .manifest import backup

version = 2

is_essential = True

managed_services = ['systemd-timesyncd']

managed_packages = []

name = _('Date & Time')

description = [
    _('Network time server is a program that maintains the system time '
      'in synchronization with servers on the Internet.')
]

manual_page = 'DateTime'

app = None


class DateTimeApp(app_module.App):
    """FreedomBox app for date and time."""

    app_id = 'datetime'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-datetime', name, None, 'fa-clock-o',
                              'datetime:index', parent_url_name='system')
        self.add(menu_item)

        daemon = Daemon('daemon-datetime', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the date/time module."""
    global app
    app = DateTimeApp()
    if app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []
    results.append(_diagnose_time_synchronized())

    return results


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
