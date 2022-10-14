# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Privacy App."""

import pathlib
from typing import Optional

import augeas

from plinth.actions import privileged

CONFIG_FILE = pathlib.Path('/etc/popularity-contest.d/freedombox.conf')


@privileged
def setup():
    """Create initial popcon configuration."""
    CONFIG_FILE.parent.mkdir(exist_ok=True)
    CONFIG_FILE.touch()

    aug = _load_augeas()
    aug.set('ENCRYPT', 'yes')
    aug.save()

    # Set the vendor to 'FreedomBox' with 'Debian' as parent
    default_link = pathlib.Path('/etc/dpkg/origins/default')
    debian_link = pathlib.Path('/etc/dpkg/origins/debian')
    if default_link.is_symlink() and default_link.resolve() == debian_link:
        default_link.unlink()
        default_link.symlink_to('freedombox')


@privileged
def set_configuration(enable_popcon: Optional[bool] = None):
    """Update popcon configuration."""
    aug = _load_augeas()
    if enable_popcon:
        aug.set('PARTICIPATE', 'yes')
    else:
        aug.set('PARTICIPATE', 'no')

    aug.save()


def get_configuration() -> dict[str, bool]:
    """Return if popcon participation is enabled."""
    aug = _load_augeas()
    value = aug.get('PARTICIPATE')
    return {'enable_popcon': (value == 'yes')}


def _load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Shellvars', str(CONFIG_FILE))
    aug.set('/augeas/context', '/files' + str(CONFIG_FILE))
    aug.load()
    return aug
