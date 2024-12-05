# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for BitTorrent web client."""

import pathlib
import shutil
import subprocess
import time

import augeas

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.deluge.utils import Config

DELUGED_DEFAULT_FILE = '/etc/default/deluged'
DELUGE_CONF_DIR = pathlib.Path('/var/lib/deluged/config/')

DELUGE_WEB_SYSTEMD_SERVICE_PATH = '/etc/systemd/system/deluge-web.service'
DELUGE_WEB_SYSTEMD_SERVICE = f'''
#
# This file is managed and overwritten by Plinth.  If you wish to edit
# it, disable Deluge in Plinth, remove this file and manage it manually.
#
[Unit]
Description=Deluge Web Interface
Documentation=man:deluge-web(1)
After=network.target
After=deluged.service

[Service]
ExecStart=/usr/bin/deluge-web --config {DELUGE_CONF_DIR} --base=deluge --do-not-daemonize
Restart=on-failure
User=debian-deluged
Group=debian-deluged
LockPersonality=yes
NoNewPrivileges=yes
PrivateDevices=yes
PrivateTmp=yes
ProtectControlGroups=yes
ProtectKernelLogs=yes
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectSystem=yes
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
RestrictRealtime=yes
StateDirectory=deluged
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
'''  # noqa: E501


def _set_configuration(filename, parameter, value):
    """Set the configuration parameter."""
    deluged_is_running = action_utils.service_is_running('deluged')
    if deluged_is_running:
        action_utils.service_stop('deluged')
    deluge_web_is_running = action_utils.service_is_running('deluge-web')
    if deluge_web_is_running:
        action_utils.service_stop('deluge-web')

    with Config(DELUGE_CONF_DIR / filename) as config:
        config.content[parameter] = value

    if deluged_is_running:
        action_utils.service_start('deluged')
    if deluge_web_is_running:
        action_utils.service_start('deluge-web')


def _get_host_id():
    """Get default host id."""
    try:
        with Config(DELUGE_CONF_DIR / 'hostlist.conf') as config:
            return config.content['hosts'][0][0]
    except FileNotFoundError:
        with Config(DELUGE_CONF_DIR / 'hostlist.conf.1.2') as config:
            return config.content['hosts'][0][0]


def _set_deluged_daemon_options():
    """Set deluged daemon options."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', DELUGED_DEFAULT_FILE)
    aug.load()
    aug.set('/files' + DELUGED_DEFAULT_FILE + '/ENABLE_DELUGED', '1')
    # overwrite daemon args, use default config directory (same as deluge-web)
    aug.set('/files' + DELUGED_DEFAULT_FILE + '/DAEMON_ARGS',
            '"-d -l /var/log/deluged/daemon.log -L info"')
    aug.save()


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
    with open(DELUGE_WEB_SYSTEMD_SERVICE_PATH, 'w',
              encoding='utf-8') as file_handle:
        file_handle.write(DELUGE_WEB_SYSTEMD_SERVICE)

    _set_deluged_daemon_options()

    subprocess.check_call(['systemctl', 'daemon-reload'])

    # Restarting an old deluge-web service stops also possible deluged process
    # that was started from the web interface.
    action_utils.service_try_restart('deluge-web')

    # Wait until core configuration is available so that status of the app can
    # be shown properly.
    _wait_for_configuration('deluged', 'core.conf')

    # Configure deluge-web to autoconnect to the default deluged daemon.
    _wait_for_configuration('deluge-web', 'web.conf')
    host_id = _get_host_id()
    _set_configuration('web.conf', 'default_daemon', host_id)


def _wait_for_configuration(service, file_name):
    """Wait until configuration file has been created."""
    conf_file = DELUGE_CONF_DIR / file_name
    if conf_file.exists():
        return

    # deluge-web creates files on first run. deluged on the other than differs
    # in version. Older version in Debian Buster creates the files after a
    # restart while newer versions create the files on first run. The following
    # approach is slightly better for create-on-exit case.
    is_running = action_utils.service_is_running(service)
    for interval in range(7):
        action_utils.service_restart(service)
        if conf_file.exists():
            break

        print('Waiting for {service} configuration')
        time.sleep(2**interval)  # Exponentially increase the time waited
    else:
        raise Exception(f'Unable to setup {service}.')

    if not is_running:
        action_utils.service_stop(service)


@privileged
def uninstall():
    """Remove configuration and service files."""
    # /etc/default/deluged is removed on purge
    pathlib.Path(DELUGE_WEB_SYSTEMD_SERVICE_PATH).unlink(missing_ok=True)
    shutil.rmtree(DELUGE_CONF_DIR, ignore_errors=True)
