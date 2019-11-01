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
Utilities for managing WireGuard.
"""

import subprocess

from plinth import network


def find_next_interface():
    """Find next unused wireguard interface name."""
    output = subprocess.check_output(['wg', 'show',
                                      'interfaces']).decode().strip()
    interfaces = output.split()
    interface_num = 1
    new_interface_name = 'wg1'
    while new_interface_name in interfaces:
        interface_num += 1
        new_interface_name = 'wg' + str(interface_num)

    return new_interface_name


def add_server(settings):
    """Add a server."""
    interface_name = find_next_interface()
    settings['common']['name'] = 'WireGuard-' + interface_name
    settings['common']['interface'] = interface_name
    network.add_connection(settings)
