#
# This file is part of Plinth.
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
Plinth module to configure system date and time
"""

from django.utils.translation import ugettext_lazy as _
import subprocess

from plinth import service as service_module
from plinth.menu import main_menu


version = 1

is_essential = True

managed_services = ['ntp']

managed_packages = ['ntp']

title = _('Date & Time')

description = [
    _('Network time server is a program that maintains the system time '
      'in synchronization with servers on the Internet.')
]

service = None


def init():
    """Intialize the date/time module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-time', 'datetime:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['ntp'], is_external=False)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['ntp'], is_external=False)
    helper.call('post', service.notify_enabled, None, True)


def diagnose():
    """Run diagnostics and return the results."""
    results = []
    results.append(_diagnose_ntp_server_count())

    return results


def _diagnose_ntp_server_count():
    """Diagnose minimum NTP server count."""
    result = 'failed'
    try:
        output = subprocess.check_output(['ntpq', '-n', '-c', 'lpeers'])
        if len(output.decode().splitlines()[2:]):
            result = 'passed'
    except subprocess.CalledProcessError:
        pass

    return [_('NTP client in contact with servers'), result]
