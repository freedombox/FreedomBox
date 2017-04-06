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
Plinth module to interface with network-manager
"""

from django.utils.translation import ugettext_lazy as _
from logging import Logger
import subprocess

from plinth import action_utils
from plinth import network
from plinth.menu import main_menu


version = 1

is_essential = True

managed_packages = ['network-manager', 'batctl']

title = _('Networks')

logger = Logger(__name__)


def init():
    """Initialize the Networks module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-signal', 'networks:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    interfaces = _get_shared_interfaces()
    addresses = _get_interface_addresses(interfaces)

    for address in addresses:
        results.append(
            action_utils.diagnose_port_listening(53, 'tcp', address))
        results.append(
            action_utils.diagnose_port_listening(53, 'udp', address))

    results.append(_diagnose_dnssec('4'))
    results.append(_diagnose_dnssec('6'))

    return results


def _get_shared_interfaces():
    """Get active network interfaces in shared mode."""
    shared_interfaces = []
    for connection in network.get_connection_list():
        if not connection['is_active']:
            continue

        connection_uuid = connection['uuid']
        connection = network.get_connection(connection_uuid)

        settings_ipv4 = connection.get_setting_ip4_config()
        if settings_ipv4.get_method() == 'shared':
            settings_connection = connection.get_setting_connection()
            interface = settings_connection.get_interface_name()
            if interface:
                shared_interfaces.append(interface)

    return shared_interfaces


def _get_interface_addresses(interfaces):
    """Get the IPv4 addresses for the given interfaces."""
    output = subprocess.check_output(['ip', '-o', 'addr'])
    lines = output.decode().splitlines()

    addresses = []
    for line in lines:
        parts = line.split()
        if parts[1] in interfaces and parts[2] == 'inet':
            addresses.append(parts[3].split('/')[0])

    return addresses


def _diagnose_dnssec(kind='4'):
    """Perform diagnostic on whether the system is using DNSSEC.

    Kind is either '4' or '6' for IPv4 and IPv6 respectively.
    """
    kind_option = {'4': '-4', '6': '-6'}[kind]

    result = 'failed'
    try:
        output = subprocess.check_output(
            ['dig', kind_option, '+time=2', '+tries=1',
             'test.dnssec-or-not.net', 'TXT'])

        if 'Yes, you are using DNSSEC' in output.decode():
            result = 'passed'
    except subprocess.CalledProcessError:
        pass

    return [_('Using DNSSEC on IPv{kind}').format(kind=kind), result]
