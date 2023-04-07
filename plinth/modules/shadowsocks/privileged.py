# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Shadowsocks."""

import json
import os
import pathlib
import random
import string
from shutil import move
from typing import Union

from plinth import action_utils
from plinth.actions import privileged

SHADOWSOCKS_CONFIG_SYMLINK = '/etc/shadowsocks-libev/freedombox.json'
SHADOWSOCKS_CONFIG_ACTUAL = \
    '/var/lib/private/shadowsocks-libev/freedombox/freedombox.json'


@privileged
def setup():
    """Perform initial setup steps."""
    # Only client socks5 proxy is supported for now. Disable the
    # server component.
    action_utils.service_disable('shadowsocks-libev')

    os.makedirs('/var/lib/private/shadowsocks-libev/freedombox/',
                exist_ok=True)

    # if existing configuration from version 1 which is normal file
    # move it to new location.
    if (not os.path.islink(SHADOWSOCKS_CONFIG_SYMLINK)
            and os.path.isfile(SHADOWSOCKS_CONFIG_SYMLINK)):
        move(SHADOWSOCKS_CONFIG_SYMLINK, SHADOWSOCKS_CONFIG_ACTUAL)

    if not os.path.islink(SHADOWSOCKS_CONFIG_SYMLINK):
        os.symlink(SHADOWSOCKS_CONFIG_ACTUAL, SHADOWSOCKS_CONFIG_SYMLINK)

    if not os.path.isfile(SHADOWSOCKS_CONFIG_ACTUAL):
        password = ''.join(
            random.choice(string.ascii_letters) for _ in range(12))
        initial_config = {
            'server': '127.0.0.1',
            'server_port': 8388,
            'local_port': 1080,
            'password': password,
            'method': 'chacha20-ietf-poly1305'
        }
        _merge_config(initial_config)

    # Commit 50e5608331330b37c0b9cce846e34ccc193d1b0d incorrectly sets the
    # StateDirectory without setting DynamicUser. Buster's shadowsocks will
    # then create directory /var/lib/shadowsocks-libev/freedombox/ and refuse
    # to delete is in later versions when DynamicUser=yes needs it to be a
    # symlink.
    action_utils.service_daemon_reload()
    wrong_state_dir = pathlib.Path('/var/lib/shadowsocks-libev/freedombox/')
    if not wrong_state_dir.is_symlink() and wrong_state_dir.is_dir():
        wrong_state_dir.rmdir()

    from plinth.modules.shadowsocks import ShadowsocksApp
    if action_utils.service_is_enabled(ShadowsocksApp.DAEMON):
        action_utils.service_restart(ShadowsocksApp.DAEMON)


@privileged
def get_config() -> dict[str, Union[int, str]]:
    """Read and print Shadowsocks configuration."""
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
def merge_config(config: dict[str, Union[int, str]]):
    """Configure Shadowsocks."""
    _merge_config(config)

    # Don't try_restart because initial configuration may not be valid so
    # shadowsocks will not be running even when enabled.
    from . import ShadowsocksApp
    if action_utils.service_is_enabled(ShadowsocksApp.DAEMON):
        action_utils.service_restart(ShadowsocksApp.DAEMON)


@privileged
def uninstall():
    """Remove configuration files."""
    for path in SHADOWSOCKS_CONFIG_SYMLINK, SHADOWSOCKS_CONFIG_ACTUAL:
        pathlib.Path(path).unlink(missing_ok=True)
