# SPDX-License-Identifier: AGPL-3.0-or-later
"""Component for managing a background daemon or any systemd unit."""

import contextlib
import socket
import subprocess

import psutil
from django.utils.translation import gettext_noop

from plinth import action_utils, app
from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)


class Daemon(app.LeaderComponent):
    """Component to manage a background daemon or any systemd unit."""

    def __init__(self, component_id: str, unit: str,
                 strict_check: bool = False,
                 listen_ports: list[tuple[int, str]] | None = None,
                 alias: str | None = None):
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

    @contextlib.contextmanager
    def ensure_running(self):
        """Ensure a service is running and return to previous state."""
        from plinth.privileged import service as service_privileged
        starting_state = self.is_running()
        if not starting_state:
            service_privileged.enable(self.unit)

        try:
            yield starting_state
        finally:
            if not starting_state:
                service_privileged.disable(self.unit)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Check if the daemon is running and listening on expected ports.

        See :py:meth:`plinth.app.Component.diagnose`.

        """
        results = []
        results.append(self._diagnose_unit_is_running())
        for port in self.listen_ports:
            results.append(diagnose_port_listening(port[0], port[1]))

        return results

    def _diagnose_unit_is_running(self) -> DiagnosticCheck:
        """Check if a daemon is running."""
        check_id = f'daemon-running-{self.unit}'
        result = Result.PASSED if self.is_running() else Result.FAILED

        description = gettext_noop('Service {service_name} is running')
        parameters: DiagnosticCheckParameters = {
            'service_name': str(self.unit)
        }

        return DiagnosticCheck(check_id, description, result, parameters)


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


class SharedDaemon(Daemon):
    """Component to manage a daemon that is used by multiple apps.

    Daemons such as a database server are a hard requirement for an app.
    However, there may be multiple apps using that server. This component
    ensures that server is enabled and running when app is enabled. It runs
    diagnostics on the daemon when app is diagnosed. The primary difference
    from the Daemon component is that when the app is disabled the daemon must
    only be disabled if there is no other app using this daemon.
    """

    # A shared daemon may be running even when an app is disabled because
    # another app might be using the daemon. Hence, the enabled/disabled state
    # of this component can't be used to determine the enabled/disabled state
    # of the app.
    is_leader = False

    def set_enabled(self, enabled):
        """Do nothing. Enabled state is still determined by unit status."""

    def disable(self):
        """Disable the daemon iff this is the last app using the daemon."""
        other_apps_enabled = False
        for other_app in app.App.list():
            if other_app.app_id == self.app_id:
                continue

            for component in other_app.get_components_of_type(SharedDaemon):
                if component.unit == self.unit and other_app.is_enabled():
                    other_apps_enabled = True

        if not other_apps_enabled:
            super().disable()


def app_is_running(app_):
    """Return whether all the daemons in the app are running."""
    for component in app_.components.values():
        if hasattr(component, 'is_running') and not component.is_running():
            return False

    return True


def diagnose_port_listening(
        port: int, kind: str = 'tcp',
        listen_address: str | None = None) -> DiagnosticCheck:
    """Run a diagnostic on whether a port is being listened on.

    Kind must be one of inet, inet4, inet6, tcp, tcp4, tcp6, udp,
    udp4, udp6, unix, all.  See psutil.net_connection() for more
    information.

    """
    result = _check_port(port, kind, listen_address)

    parameters: DiagnosticCheckParameters = {'kind': kind, 'port': port}
    if listen_address:
        parameters['listen_address'] = listen_address
        check_id = f'daemon-listening-address-{kind}-{port}-{listen_address}'
        description = gettext_noop(
            'Listening on {kind} port {listen_address}:{port}')
    else:
        check_id = f'daemon-listening-{kind}-{port}'
        description = gettext_noop('Listening on {kind} port {port}')

    return DiagnosticCheck(check_id, description,
                           Result.PASSED if result else Result.FAILED,
                           parameters)


def _check_port(port: int, kind: str = 'tcp',
                listen_address: str | None = None) -> bool:
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
        if connection.laddr[1] != port:  # type: ignore[misc]
            continue

        # Listen address if requested should match
        if listen_address and connection.laddr[
                0] != listen_address:  # type: ignore[misc]
            continue

        # Special additional checks only for IPv4
        if kind not in ('tcp4', 'udp4'):
            return True

        # Found socket is IPv4
        if connection.family == socket.AF_INET:
            return True

        # Full IPv6 address range includes mapped IPv4 address also
        if connection.laddr[0] == '::':  # type: ignore[misc]
            return True

    return False


def diagnose_netcat(host: str, port: int, remote_input: str = '',
                    negate: bool = False) -> DiagnosticCheck:
    """Run a diagnostic using netcat."""
    try:
        process = subprocess.Popen(['nc', host, str(port)],
                                   stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.communicate(input=remote_input.encode())
        if process.returncode != 0:
            result = Result.FAILED if not negate else Result.PASSED
        else:
            result = Result.PASSED if not negate else Result.FAILED
    except Exception:
        result = Result.FAILED

    check_id = f'daemon-netcat-{host}-{port}'
    description = gettext_noop('Connect to {host}:{port}')
    parameters: DiagnosticCheckParameters = {
        'host': host,
        'port': port,
        'negate': negate
    }
    if negate:
        check_id = f'daemon-netcat-negate-{host}-{port}'
        description = gettext_noop('Cannot connect to {host}:{port}')

    return DiagnosticCheck(check_id, description, result, parameters)
