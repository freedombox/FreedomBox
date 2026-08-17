# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Minetest server."""

import pathlib
import shutil

import augeas

from plinth import action_utils
from plinth.actions import privileged

old_config_file = pathlib.Path('/etc/minetest/minetest.conf')
config_file = pathlib.Path('/etc/luanti/default.conf')
AUG_PATH = '/files' + str(config_file) + '/.anon'


@privileged
def setup() -> None:
    """Migrate old configuration file."""
    if old_config_file.exists():
        old_config_file.rename(config_file)
        action_utils.service_daemon_reload()
        action_utils.service_try_restart('luanti-server')


@privileged
def configure(max_players: int | None = None, enable_pvp: bool | None = None,
              creative_mode: bool | None = None,
              enable_damage: bool | None = None):
    """Update configuration file and restart daemon if necessary."""
    config_file.parent.mkdir(exist_ok=True)
    aug = load_augeas()
    if max_players is not None:
        aug.set(AUG_PATH + '/max_users', str(max_players))

    if enable_pvp is not None:
        aug.set(AUG_PATH + '/enable_pvp', str(enable_pvp).lower())

    if creative_mode is not None:
        aug.set(AUG_PATH + '/creative_mode', str(creative_mode).lower())

    if enable_damage is not None:
        aug.set(AUG_PATH + '/enable_damage', str(enable_damage).lower())

    aug.save()
    action_utils.service_try_restart('luanti-server')


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Php/lens', 'Php.lns')
    aug.set('/augeas/load/Php/incl[last() + 1]', str(config_file))
    aug.load()
    return aug


@privileged
def uninstall() -> None:
    """Remove the data directory that luanti-server package fails to remove.

    See: https://bugs.debian.org/1122677
    """
    shutil.rmtree('/var/lib/private/luanti/default/')
