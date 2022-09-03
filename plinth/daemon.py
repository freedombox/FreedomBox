# SPDX-License-Identifier: AGPL-3.0-or-later
"""Component for managing a background daemon or any systemd unit."""

import socket
import subprocess

import psutil
from django.utils.text import format_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from plinth import action_utils, app


class Daemon(app.LeaderComponent):
    """Component to manage a background daemon or any systemd unit."""

    def __init__(self, component_id, unit, strict_check=False,
                 listen_ports=None, alias=None):
        """Initialize a new daemon component.

        'component_id' must be a unique string across all apps and components
        of a app. Conventionally starts with 'daemon-'.

        'unit' must the name of systemd unit that this component should manage.

        'listen_ports' is a list of tuples. Each tuple contains the port number
        as integer followed by a string with one of the values 'tcp4', 'tcp6',
        'tcp', 'udp4', 'udp6', 'udp' indicating the protocol that the daemon
        listens on. This information is used to run diagnostic tests.

        'alias' is an alternate name for the same unit file. When a unit file
        is renamed, the new unit file usually contains an Alias= setting in
        [Install] section with value of old unit name. When the unit is
        enabled, a symlink with the name of the alias is created. All
        operations such as is-running and disable work with the alias along
        with the primary unit name. However, for the case of enabling the unit
        file or checking its enabled status, the alias does not work. To be
        able to provide management for multiple versions of the unit file with
        different names, specify an alias. Both the names are taken into
        consideration when enabling the unit file.

        """
        super().__init__(component_id)

        self.unit = unit
        self.strict_check = strict_check
        self.listen_ports = listen_ports or []
        self.alias = alias

    def is_enabled(self):
        """Return if the daemon/unit is enabled."""
        if self.alias:
            # XXX: Handling alias should not be done here. service_is_enabled()
            # should return True even for an alias. Currently, in addition to
            # return code we are also checking the printed value. This makes
            # the implementation less future-proof as new values could printed
            # by the command. A fixed systemd bug
            # https://github.com/systemd/systemd/issues/18134 also currently
            # gives incorrect exit code for 'alias' case. See:
            # https://salsa.debian.org/freedombox-team/freedombox/-/merge_requests/1980
            if action_utils.service_is_enabled(self.alias,
                                               strict_check=self.strict_check):
                return True

        return action_utils.service_is_enabled(self.unit,
                                               strict_check=self.strict_check)

    def enable(self):
        """Run operations to enable the daemon/unit."""
        from plinth.privileged import service as service_privileged
        service_privileged.enable(self.unit)
        if self.alias:
            service_privileged.enable(self.alias)

    def disable(self):
        """Run operations to disable the daemon/unit."""
        from plinth.privileged import service as service_privileged
        service_privileged.disable(self.unit)
        if self.alias:
            service_privileged.disable(self.alias)

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
        result = 'passed' if self.is_running() else 'failed'

        template = gettext_lazy('Service {service_name} is running')
        testname = format_lazy(template, service_name=self.unit)

        return [testname, result]


class RelatedDaemon(app.FollowerComponent):
    """Component to hold information about additional systemd units handled.

    Unlike a daemon described by the Daemon component which is enabled/disabled
    when the app is enabled/disabled, the daemon described by this component is
    unaffected by the app's enabled/disabled status. The app only has an
    indirect interest in this daemon.

    This component primarily holds information about such daemon and does
    nothing else. This information is used to check if the app is allowed to
    perform operations on the daemon.
    """

    def __init__(self, component_id, unit):
        """Initialize a new related daemon component.

        'component_id' must be a unique string across all apps and components
        of a app. Conventionally starts with 'related-daemon-'.

        'unit' must the name of systemd unit.

        """
        super().__init__(component_id)

        self.unit = unit


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
        template = gettext_lazy(
            'Listening on {kind} port {listen_address}:{port}')
        testname = format_lazy(template, kind=kind,
                               listen_address=listen_address, port=port)
    else:
        template = gettext_lazy('Listening on {kind} port {port}')
        testname = format_lazy(template, kind=kind, port=port)

    return [testname, 'passed' if result else 'failed']


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
