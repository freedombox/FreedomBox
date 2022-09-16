# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure miscellaneous system settings."""

import pathlib

import augeas

from plinth import action_utils
from plinth.actions import privileged

JOURNALD_FILE = pathlib.Path('/etc/systemd/journald.conf.d/50-freedombox.conf')


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Puppet', str(JOURNALD_FILE))
    aug.set('/augeas/context', '/files' + str(JOURNALD_FILE))
    aug.load()
    return aug


def get_logging_mode() -> str:
    """Return the logging mode as none, volatile or persistent."""
    aug = load_augeas()
    storage = aug.get('Journal/Storage')
    if storage in ('volatile', 'persistent', 'none'):
        return storage

    # journald's default is 'auto'. On Debian systems, 'auto' is same
    # 'persistent' because /var/log/journal exists by default.
    return 'persistent'


@privileged
def set_logging_mode(mode: str):
    """Set the current logging mode."""
    if mode not in ('volatile', 'persistent', 'none'):
        raise ValueError('Invalid mode')

    aug = load_augeas()
    aug.set('Journal/Storage', mode)
    if mode == 'volatile':
        aug.set('Journal/RuntimeMaxUse', '5%')
        aug.set('Journal/MaxFileSec', '6h')
        aug.set('Journal/MaxRetentionSec', '2day')
    else:
        aug.remove('Journal/RuntimeMaxUse')
        aug.remove('Journal/MaxFileSec')
        aug.remove('Journal/MaxRetentionSec')

    JOURNALD_FILE.parent.mkdir(exist_ok=True)
    aug.save()

    # systemd-journald is socket activated, it may not be running and it does
    # not support reload.
    action_utils.service_try_restart('systemd-journald')
