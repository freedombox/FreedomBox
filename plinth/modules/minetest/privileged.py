# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Minetest server."""

from typing import Optional

import augeas

from plinth import action_utils
from plinth.actions import privileged

CONFIG_FILE = '/etc/minetest/minetest.conf'
AUG_PATH = '/files' + CONFIG_FILE + '/.anon'


@privileged
def configure(max_players: Optional[int] = None,
              enable_pvp: Optional[bool] = None,
              creative_mode: Optional[bool] = None,
              enable_damage: Optional[bool] = None):
    """Update configuration file and restart daemon if necessary."""
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
    action_utils.service_try_restart('minetest-server')


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Php/lens', 'Php.lns')
    aug.set('/augeas/load/Php/incl[last() + 1]', CONFIG_FILE)
    aug.load()
    return aug
