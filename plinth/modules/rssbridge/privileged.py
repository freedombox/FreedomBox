# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure RSS-Bridge."""

import pathlib
from plinth import action_utils

from plinth.actions import privileged

PUBLIC_ACCESS_FILE = '/etc/rss-bridge/is_public'


@privileged
def setup():
    """Configure RSS-Bridge by enable all bridges."""
    enable_list = pathlib.Path('/etc/rss-bridge/whitelist.txt')
    enable_list.write_text('*\n', encoding='utf-8')


@privileged
def set_public(enable: bool):
    """Allow/disallow public access."""
    public_access_file = pathlib.Path(PUBLIC_ACCESS_FILE)
    if enable:
        public_access_file.touch()
    else:
        public_access_file.unlink(missing_ok=True)

    action_utils.service_reload('apache2')


def is_public() -> bool:
    """Return whether public access is enabled."""
    return pathlib.Path(PUBLIC_ACCESS_FILE).exists()
