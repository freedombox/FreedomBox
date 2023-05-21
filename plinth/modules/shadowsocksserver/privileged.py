# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Shadowsocks Server."""

import json
import os
import pathlib
import random
import string
from typing import Union

from plinth import action_utils
from plinth.actions import privileged

SHADOWSOCKS_CONFIG_SYMLINK = '/etc/shadowsocks-libev/fbxserver.json'
SHADOWSOCKS_CONFIG_ACTUAL = \
    '/var/lib/private/shadowsocks-libev/fbxserver/fbxserver.json'


@privileged
def setup():
    """Perform initial setup steps."""
    # Disable the default service, and use the templated service instead, so
    # that the configuration can be customized.
    action_utils.service_disable('shadowsocks-libev')

    os.makedirs('/var/lib/private/shadowsocks-libev/fbxserver/', exist_ok=True)

    if not os.path.islink(SHADOWSOCKS_CONFIG_SYMLINK):
        os.symlink(SHADOWSOCKS_CONFIG_ACTUAL, SHADOWSOCKS_CONFIG_SYMLINK)

    if not os.path.isfile(SHADOWSOCKS_CONFIG_ACTUAL):
        password = ''.join(
            random.choice(string.ascii_letters) for _ in range(12))
        initial_config = {
            'server': ['::0', '0.0.0.0'],  # As recommended in man page
            'mode': 'tcp_and_udp',
            'server_port': 8388,
            'password': password,
            'timeout': 86400,
            'method': 'chacha20-ietf-poly1305'
        }
        _merge_config(initial_config)

    from plinth.modules.shadowsocksserver import ShadowsocksServerApp
    if action_utils.service_is_enabled(ShadowsocksServerApp.DAEMON):
        action_utils.service_restart(ShadowsocksServerApp.DAEMON)


@privileged
def get_config() -> dict[str, Union[int, str]]:
    """Read and print Shadowsocks Server configuration."""
    config = open(SHADOWSOCKS_CONFIG_SYMLINK, 'r', encoding='utf-8').read()
    return json.loads(config)


def _merge_config(config):
    """Write merged configuration into file."""
    try:
        current_config = open(SHADOWSOCKS_CONFIG_SYMLINK, 'r',
                              encoding='utf-8').read()
        current_config = json.loads(current_config)
    except (OSError, json.JSONDecodeError):
        current_config = {}

    new_config = current_config
    new_config.update(config)
    new_config = json.dumps(new_config, indent=4, sort_keys=True)
    open(SHADOWSOCKS_CONFIG_SYMLINK, 'w', encoding='utf-8').write(new_config)


@privileged
def merge_config(config: dict[str, str]):
    """Configure Shadowsocks Server."""
    _merge_config(config)

    # Don't try_restart because initial configuration may not be valid so
    # shadowsocks will not be running even when enabled.
    from . import ShadowsocksServerApp
    if action_utils.service_is_enabled(ShadowsocksServerApp.DAEMON):
        action_utils.service_restart(ShadowsocksServerApp.DAEMON)


@privileged
def uninstall():
    """Remove configuration files."""
    for path in SHADOWSOCKS_CONFIG_SYMLINK, SHADOWSOCKS_CONFIG_ACTUAL:
        pathlib.Path(path).unlink(missing_ok=True)
