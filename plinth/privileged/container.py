# SPDX-License-Identifier: AGPL-3.0-or-later
"""Handle container run using podman."""

from plinth import action_utils
from plinth import app as app_module
from plinth import module_loader
from plinth.actions import privileged


@privileged
def container_is_enabled(container: str) -> bool:
    """Return whether a container is enabled."""
    _assert_container_is_managed(container)
    return action_utils.podman_is_enabled(container)


@privileged
def container_enable(container: str):
    """Enable a container so that it start on system boot."""
    _assert_container_is_managed(container)
    action_utils.podman_enable(container)
    action_utils.service_enable(container)


@privileged
def container_disable(container: str):
    """Disable a container so that it does not start on system boot."""
    _assert_container_is_managed(container)
    action_utils.service_disable(container)
    action_utils.podman_disable(container)


@privileged
def container_setup(container: str, image_name: str, volume_name: str,
                    volume_path: str, volumes: dict[str, str] | None = None,
                    env: dict[str, str] | None = None,
                    binds_to: list[str] | None = None,
                    devices: dict[str, str] | None = None):
    """Remove and recreate the podman container."""
    _assert_container_is_managed(container)
    action_utils.podman_create(container, image_name, volume_name, volume_path,
                               volumes, env, binds_to, devices)
    action_utils.service_start(container, check=True)


@privileged
def container_uninstall(container: str, image_name: str, volume_name: str,
                        volume_path: str):
    """Remove podman container."""
    action_utils.podman_uninstall(container_name=container,
                                  image_name=image_name,
                                  volume_name=volume_name,
                                  volume_path=volume_path)


def _get_managed_containers() -> set[str]:
    """Get a set of all containers managed by FreedomBox."""
    from plinth.container import Container

    containers = set()
    module_loader.load_modules()
    app_module.apps_init()
    for app in app_module.App.list():
        components = app.get_components_of_type(Container)
        for component in components:
            containers.add(component.name)

    return containers


def _assert_container_is_managed(container_name):
    """Check that container is managed by one of the FreedomBox apps."""
    managed_containers = _get_managed_containers()
    if container_name not in managed_containers:
        msg = ("The container '%s' is not managed by FreedomBox. Access is "
               "only permitted for containers listed in the Container "
               "components of any FreedomBox app.") % container_name
        raise ValueError(msg)
