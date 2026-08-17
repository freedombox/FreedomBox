# SPDX-License-Identifier: AGPL-3.0-or-later
"""Shutdown/restart the system."""

from plinth import action_utils
from plinth.actions import privileged


@privileged
def restart():
    """Restart the system."""
    action_utils.run('reboot', check=False)


@privileged
def shutdown():
    """Shut down the system."""
    action_utils.run(['shutdown', 'now'], check=False)
