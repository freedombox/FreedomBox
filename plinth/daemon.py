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
Component for managing a background daemon or any systemd unit.
"""

import socket
import subprocess

import psutil
from django.utils.translation import ugettext as _

from plinth import action_utils, actions, app


class Daemon(app.LeaderComponent):
    """Component to manage a background daemon or any systemd unit."""
    def __init__(self, component_id, unit, strict_check=False,
                 listen_ports=None):
        """Initialize a new daemon component.

        'component_id' must be a unique string across all apps and components
        of a app. Conventionally starts with 'daemon-'.

        'unit' must the name of systemd unit that this component should manage.

        'listen_ports' is a list of tuples. Each tuple contains the port number
        as integer followed by a string with one of the values 'tcp4', 'tcp6',
        'tcp', 'udp4', 'udp6', 'udp' indicating the protocol that the daemon
        listens on. This information is used to run diagnostic tests.

        """
        super().__init__(component_id)

        self.unit = unit
        self.strict_check = strict_check
        self.listen_ports = listen_ports or []

    def is_enabled(self):
        """Return if the daemon/unit is enabled."""
        return action_utils.service_is_enabled(self.unit,
                                               strict_check=self.strict_check)

    def enable(self):
        """Run operations to enable the daemon/unit."""
        actions.superuser_run('service', ['enable', self.unit])

    def disable(self):
        """Run operations to disable the daemon/unit."""
        actions.superuser_run('service', ['disable', self.unit])

    def is_running(self):
        """Return whether the daemon/unit is running."""
        return action_utils.service_is_running(self.unit)

    def diagnose(self):
        """Check if the daemon is running and listening on expected ports.

        See :py:meth:`plinth.app.Component.diagnose`.

        """
        results = []
        results.append(self._diagnose_unit_is_running())
        for port in self.listen_ports:
            results.append(diagnose_port_listening(port[0], port[1]))

        return results

    def _diagnose_unit_is_running(self):
        """Check if a daemon is running."""
        message = _('Service {service_name} is running').format(
            service_name=self.unit)
        result = 'passed' if self.is_running() else 'failed'
        return [message, result]


def app_is_running(app_):
    """Return whether all the daemons in the app are running."""
    for component in app_.components.values():
        if hasattr(component, 'is_running') and not component.is_running():
            return False

    return True


def diagnose_port_listening(port, kind='tcp', listen_address=None):
    """Run a diagnostic on whether a port is being listened on.

    Kind must be one of inet, inet4, inet6, tcp, tcp4, tcp6, udp,
    udp4, udp6, unix, all.  See psutil.net_connection() for more
    information.

    """
    result = _check_port(port, kind, listen_address)

    if listen_address:
        test = _('Listening on {kind} port {listen_address}:{port}') \
               .format(kind=kind, listen_address=listen_address, port=port)
    else:
        test = _('Listening on {kind} port {port}') \
               .format(kind=kind, port=port)

    return [test, 'passed' if result else 'failed']


def _check_port(port, kind='tcp', listen_address=None):
    """Return whether a port is being listened on."""
    run_kind = kind

    if kind == 'tcp4':
        run_kind = 'tcp'

    if kind == 'udp4':
        run_kind = 'udp'

    for connection in psutil.net_connections(run_kind):
        # TCP connections must have status='listen'
        if kind in ('tcp', 'tcp4', 'tcp6') and \
           connection.status != psutil.CONN_LISTEN:
            continue

        # UDP connections must have empty remote address
        if kind in ('udp', 'udp4', 'udp6') and \
           connection.raddr != ():
            continue

        # Port should match
        if connection.laddr[1] != port:
            continue

        # Listen address if requested should match
        if listen_address and connection.laddr[0] != listen_address:
            continue

        # Special additional checks only for IPv4
        if kind not in ('tcp4', 'udp4'):
            return True

        # Found socket is IPv4
        if connection.family == socket.AF_INET:
            return True

        # Full IPv6 address range includes mapped IPv4 address also
        if connection.laddr[0] == '::':
            return True

    return False


def diagnose_netcat(host, port, input='', negate=False):
    """Run a diagnostic using netcat."""
    try:
        process = subprocess.Popen(['nc', host, str(port)],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate(input=input.encode())
        if process.returncode != 0:
            result = 'failed'
        else:
            result = 'passed'

        if negate:
            result = 'failed' if result == 'passed' else 'passed'
    except Exception:
        result = 'failed'

    test = _('Connect to {host}:{port}')
    if negate:
        test = _('Cannot connect to {host}:{port}')

    return [test.format(host=host, port=port), result]
