# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure I2P."""

from plinth.actions import privileged
from plinth.modules.i2p.helpers import RouterEditor, TunnelEditor


@privileged
def set_tunnel_property(name: str, property_: str, value: str):
    """Modify the configuration file for a certain tunnel."""
    editor = TunnelEditor()
    editor \
        .read_conf() \
        .set_tunnel_idx(name) \
        .set_tunnel_prop(property_, value) \
        .write_conf()


@privileged
def add_favorite(name: str, url: str, description: str | None,
                 icon: str | None):
    """Add a favorite to router.config."""
    editor = RouterEditor()
    editor.read_conf().add_favorite(name, url, description, icon).write_conf()
