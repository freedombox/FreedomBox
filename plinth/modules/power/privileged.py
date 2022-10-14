# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shutdown/restart the system."""

import subprocess

from plinth.actions import privileged


@privileged
def restart():
    """Restart the system."""
    subprocess.call('reboot')


@privileged
def shutdown():
    """Shut down the system."""
    subprocess.call(['shutdown', 'now'])
