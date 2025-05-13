# SPDX-License-Identifier: AGPL-3.0-or-later
"""Component to manage a container using podman."""

import contextlib

from django.utils.translation import gettext_noop

from plinth import app, privileged
from plinth.daemon import diagnose_port_listening
from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)


class Container(app.LeaderComponent):
    """Component to manage a podman container."""

    def __init__(self, component_id: str, name: str, image_name: str,
                 volume_name: str, volume_path: str,
                 volumes: dict[str, str] | None = None,
                 env: dict[str, str] | None = None,
                 binds_to: list[str] | None = None,
                 devices: dict[str, str] | None = None,
                 listen_ports: list[tuple[int, str]] | None = None):
        """Initialize a container component.

        `name` is a string which is the name of the container to create and
        manage. A systemd service unit with the same name is also created.

        `image_name` is a string that represents the repository location from
        which the container images must be pull from.

        `volume_name` is a string with name of the storage volume to create for
        the container to use.

        `volume_path` is a string path on the host machine where the volume
        files for the container is stored.

        `volumes` is a dictionary mapping each string path on the host to a
        string path inside the container. These are bind mounts made available
        inside the container.

        `env` is a dictionary of string key to string values that set the
        environment variables for the processes inside the container to run in.

        `binds_to` is a list of systemd service units that the container's own
        systemd service unit will add BindsTo= and After= dependencies on.

        `devices` is a list of strings with device paths that will be made
        available inside the container. If any of the devices don't exist on
        the host, they will not be added.

        `listen_ports` is a list of tuples containing port number and 'tcp4' or
        'tcp6' network types on which this container is expected to listen on
        after starting the container. This information is used to run
        diagnostic checks on the container.
        """
        super().__init__(component_id)
        self.name = name
        self.image_name = image_name
        self.volume_name = volume_name
        self.volume_path = volume_path
        self.volumes = volumes
        self.env = env
        self.binds_to = binds_to
        self.devices = devices
        self.listen_ports = listen_ports or []

    def is_enabled(self):
        """Return if the container is enabled."""
        return privileged.container_is_enabled(self.name)

    def enable(self):
        """Run operations to enable and run the container."""
        super().enable()
        privileged.container_enable(self.name)

    def disable(self):
        """Run operations to disable and stop the container."""
        super().disable()
        privileged.container_disable(self.name)

    def is_running(self):
        """Return whether the container service is running."""
        return privileged.is_running(self.name)

    @contextlib.contextmanager
    def ensure_running(self):
        """Ensure a service is running and return to previous state."""
        from plinth.privileged import service as service_privileged
        starting_state = self.is_running()
        if not starting_state:
            service_privileged.enable(self.name)

        try:
            yield starting_state
        finally:
            if not starting_state:
                service_privileged.disable(self.name)

    def setup(self, old_version: int):
        """Bring up and run the container."""
        # Determine whether app should be disabled after setup
        should_disable = old_version and not self.is_enabled()

        privileged.container_setup(self.name, self.image_name,
                                   self.volume_name, self.volume_path,
                                   self.volumes, self.env, self.binds_to,
                                   self.devices)

        if should_disable:
            self.disable()

    def uninstall(self):
        """Remove the container."""
        privileged.container_uninstall(self.name, self.image_name,
                                       self.volume_name, self.volume_path)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Check if the container is running..

        See :py:meth:`plinth.app.Component.diagnose`.
        """
        results = []
        results.append(self._diagnose_unit_is_running())
        for port in self.listen_ports:
            results.append(
                diagnose_port_listening(port[0], port[1], None,
                                        self.component_id))

        return results

    def _diagnose_unit_is_running(self) -> DiagnosticCheck:
        """Check if a daemon is running."""
        check_id = f'container-running-{self.name}'
        result = Result.PASSED if self.is_running() else Result.FAILED

        description = gettext_noop('Container {container_name} is running')
        parameters: DiagnosticCheckParameters = {
            'container_name': str(self.name)
        }

        return DiagnosticCheck(check_id, description, result, parameters,
                               self.component_id)
