# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure RSS-Bridge."""

import pathlib

from plinth.actions import privileged


@privileged
def setup():
    """Configure RSS-Bridge by enable all bridges."""
    enable_list = pathlib.Path('/etc/rss-bridge/whitelist.txt')
    enable_list.write_text('*\n', encoding='utf-8')
