# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for BitTorrent web client."""

import pathlib
import shutil
import time

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.deluge.utils import Config

DELUGE_CONF_DIR = pathlib.Path('/var/lib/deluged/config/')


def _set_configuration(filename, parameter, value):
    """Set the configuration parameter."""
    with action_utils.service_ensure_stopped('deluge-web'):
        with action_utils.service_ensure_stopped('deluged'):
            with Config(DELUGE_CONF_DIR / filename) as config:
                config.content[parameter] = value


def _get_host_id():
    """Get default host id."""
    try:
        with Config(DELUGE_CONF_DIR / 'hostlist.conf') as config:
            return config.content['hosts'][0][0]
    except FileNotFoundError:
        with Config(DELUGE_CONF_DIR / 'hostlist.conf.1.2') as config:
            return config.content['hosts'][0][0]


@privileged
def get_configuration() -> dict[str, str]:
    """Return the current deluged configuration."""
    with Config(DELUGE_CONF_DIR / 'core.conf') as config:
        download_location = config.content['download_location']

    return {'download_location': download_location}


@privileged
def set_configuration(download_location: str):
    """Set the deluged configuration."""
    _set_configuration('core.conf', 'download_location', download_location)


@privileged
def setup():
    """Perform initial setup for deluge."""
    old_service_path = pathlib.Path('/etc/systemd/system/deluge-web.service')
    if old_service_path.exists():
        old_service_path.unlink(missing_ok=True)

    action_utils.service_daemon_reload()
    action_utils.service_try_restart('deluged')
    action_utils.service_try_restart('deluge-web')

    # Wait until core configuration is available so that status of the app can
    # be shown properly.
    _wait_for_configuration()

    # Configure deluge-web to autoconnect to the default deluged daemon.
    host_id = _get_host_id()
    _set_configuration('web.conf', 'default_daemon', host_id)


def _wait_for_configuration():
    """Wait until configuration file has been created."""
    core_file = DELUGE_CONF_DIR / 'core.conf'
    web_file = DELUGE_CONF_DIR / 'web.conf'
    if core_file.exists() and web_file.exists():
        return

    # deluge-web and deluged create files on first run.
    with action_utils.service_ensure_running('deluged'):
        with action_utils.service_ensure_running('deluge-web'):
            for _ in range(60):
                if core_file.exists() and web_file.exists():
                    break

                time.sleep(1)
            else:
                raise Exception('Unable to setup configuration')


@privileged
def uninstall():
    """Remove configuration and service files."""
    # /etc/default/deluged is removed on purge
    shutil.rmtree(DELUGE_CONF_DIR, ignore_errors=True)
