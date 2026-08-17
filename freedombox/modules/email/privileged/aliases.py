# SPDX-License-Identifier: AGPL-3.0-or-later
"""Privileged operations for managing aliases."""

import pathlib
import shutil

from plinth.actions import privileged


@privileged
def setup_aliases():
    """Create a the sqlite3 database to be managed by FreedomBox."""
    path = pathlib.Path('/var/lib/postfix/freedombox-aliases/')
    path.mkdir(mode=0o750, exist_ok=True)
    shutil.chown(path, user='plinth', group='postfix')
