# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Shaarli."""

import shutil

from plinth.actions import privileged


@privileged
def uninstall():
    """Remove Shaarli's data directory."""
    shutil.rmtree('/var/lib/shaarli/data', ignore_errors=True)
