# SPDX-License-Identifier: AGPL-3.0-or-later
"""Actions for help module."""

import subprocess

from plinth.actions import privileged


@privileged
def get_logs() -> str:
    """Get latest FreedomBox logs."""
    command = ['journalctl', '--no-pager', '--lines=100', '--unit=plinth']
    process = subprocess.run(command, check=True, stdout=subprocess.PIPE)
    return process.stdout.decode()
