# SPDX-License-Identifier: AGPL-3.0-or-later
"""List and handle system services."""

from plinth import action_utils
from plinth import app as app_module
from plinth import module_loader
from plinth.actions import privileged
from plinth.daemon import Daemon, RelatedDaemon


@privileged
def systemd_set_default(target: str):
    """Set the default target that systemd will boot into."""
    if target not in ['graphical.target', 'multi-user.target']:
        raise ValueError('Invalid target')

    action_utils.systemd_set_default(target)


@privileged
def start(service: str):
    """Start a service."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_start(service)


@privileged
def stop(service: str):
    """Stop a running service."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_stop(service)


@privileged
def enable(service: str):
    """Enable a service so that it start on system boot."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_enable(service)


@privileged
def disable(service: str):
    """Disable a service so that it does not start on system boot."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_disable(service)


@privileged
def restart(service: str):
    """Restart a service."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_restart(service)


@privileged
def try_restart(service: str):
    """Restart a service if it is running."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_try_restart(service)


@privileged
def reload(service: str):
    """Reload a service."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_reload(service)


@privileged
def try_reload_or_restart(service: str):
    """Reload a service if it supports reloading, otherwise restart.

    Do nothing if service is not running.
    """
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_try_reload_or_restart(service)


@privileged
def mask(service: str):
    """Mask a service."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_mask(service)


@privileged
def unmask(service: str):
    """Unmask a service."""
    _assert_service_is_managed_by_plinth(service)
    action_utils.service_unmask(service)


@privileged
def is_enabled(service: str) -> bool:
    """Return whether a service is enabled."""
    _assert_service_is_managed_by_plinth(service)
    return action_utils.service_is_enabled(service)


@privileged
def is_running(service: str) -> bool:
    """Return whether a service is running."""
    _assert_service_is_managed_by_plinth(service)
    return action_utils.service_is_running(service)


def _get_managed_services():
    """Get a set of all services managed by FreedomBox."""
    services = set()
    module_loader.load_modules()
    app_module.apps_init()
    for app in app_module.App.list():
        components = app.get_components_of_type(Daemon)
        for component in components:
            services.add(component.unit)
            if component.alias:
                services.add(component.alias)

        components = app.get_components_of_type(RelatedDaemon)
        for component in components:
            services.add(component.unit)

    return services


def _assert_service_is_managed_by_plinth(service_name):
    managed_services = _get_managed_services()
    if service_name not in managed_services:
        msg = ("The service '%s' is not managed by FreedomBox. Access is only "
               "permitted for services listed in the Daemon and RelatedDaemon "
               "components of any FreedomBox app.") % service_name
        raise ValueError(msg)
