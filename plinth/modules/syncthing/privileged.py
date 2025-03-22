# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Syncthing."""

import grp
import os
import pwd
import shutil
import subprocess
import time

import augeas

from plinth import action_utils
from plinth.actions import privileged

DATA_DIR = '/var/lib/syncthing'
# legacy configuration file
CONF_FILE_LEGACY = DATA_DIR + '/.config/syncthing/config.xml'
# configuration file since Debian Trixie if '.config/syncthing' directory
# doesn't exist
CONF_FILE = DATA_DIR + '/.local/state/syncthing/config.xml'


def augeas_load(conf_file):
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.add_transform('Xml.lns', conf_file)
    aug.load()
    return aug


@privileged
def setup():
    """Perform post-install actions for Syncthing."""
    # Create syncthing group if needed.
    try:
        grp.getgrnam('syncthing')
    except KeyError:
        subprocess.run(['addgroup', '--system', 'syncthing'], check=True)

    # Create syncthing user if needed.
    try:
        pwd.getpwnam('syncthing')
    except KeyError:
        subprocess.run([
            'adduser', '--system', '--ingroup', 'syncthing', '--home',
            DATA_DIR, '--gecos', 'Syncthing file synchronization server',
            'syncthing'
        ], check=True)

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, mode=0o750)
        shutil.chown(DATA_DIR, user='syncthing', group='syncthing')


@privileged
def setup_config():
    """Make configuration changes."""
    # wait until the configuration file is created by the syncthing daemon
    conf_file_in_use = CONF_FILE
    timeout = 300
    while timeout > 0:
        if os.path.exists(CONF_FILE_LEGACY):
            conf_file_in_use = CONF_FILE_LEGACY
            break
        elif os.path.exists(CONF_FILE):
            break
        timeout = timeout - 1
        time.sleep(1)

    aug = augeas_load(conf_file_in_use)

    # disable authentication missing notification as FreedomBox itself
    # provides authentication
    # also make sure no authentication is required on top of FreedomBox's
    configs_to_remove = (
        'options/unackedNotificationID[#text="authenticationUserAndPassword"]',
        'gui/user/#text', 'gui/password/#text')
    conf_changed = False
    for config in configs_to_remove:
        removed = bool(
            aug.remove('/files' + conf_file_in_use +
                       f'/configuration/{config}'))
        if removed:
            conf_changed = True

    configs = {
        # disable usage reporting notification by declining reporting
        # if the user has not made a choice yet
        'options/urAccepted/#text': '-1',
        # Set all the values that, misconfigured from the Syncthing UI,
        # can make the UI inaccessible. Such misconfigurations can be
        # corrected if the user re-runs the setup.
        # https://discuss.freedombox.org/t/solved-cant-access-syncthing-administration-panel/2137
        'gui/#attribute/tls': 'false',
        'gui/#attribute/enabled': 'true',
        'gui/address/#text': '127.0.0.1:8384'
    }
    for key, value in configs.items():
        config = f'/configuration/{key}'
        if aug.get('/files' + conf_file_in_use + config) != value:
            aug.set('/files' + conf_file_in_use + config, value)
            conf_changed = True

    aug.save()

    if conf_changed:
        action_utils.service_try_restart('syncthing@syncthing')


@privileged
def uninstall():
    """Remove configuration directory when app is uninstalled."""
    # legacy location
    shutil.rmtree(DATA_DIR + '/.config', ignore_errors=True)
    shutil.rmtree(DATA_DIR + '/.local', ignore_errors=True)
