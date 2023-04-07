# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure RSS-Bridge."""

import pathlib

from plinth import action_utils
from plinth.actions import privileged

PUBLIC_ACCESS_FILE = pathlib.Path('/etc/rss-bridge/is_public')
ENABLE_LIST = pathlib.Path('/etc/rss-bridge/whitelist.txt')


@privileged
def setup():
    """Configure RSS-Bridge by enable all bridges."""
    ENABLE_LIST.write_text('*\n', encoding='utf-8')


@privileged
def set_public(enable: bool):
    """Allow/disallow public access."""
    if enable:
        PUBLIC_ACCESS_FILE.touch()
    else:
        PUBLIC_ACCESS_FILE.unlink(missing_ok=True)

    action_utils.service_reload('apache2')


def is_public() -> bool:
    """Return whether public access is enabled."""
    return PUBLIC_ACCESS_FILE.exists()


@privileged
def uninstall():
    """Remove config files when app is uninstalled."""
    for path in PUBLIC_ACCESS_FILE, ENABLE_LIST:
        path.unlink(missing_ok=True)
