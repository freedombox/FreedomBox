# SPDX-License-Identifier: AGPL-3.0-or-later
"""Set time zone with timedatectl."""

from freedombox import action_utils
from freedombox.actions import privileged


@privileged
def set_timezone(timezone: str):
    """Set time zone with timedatectl."""
    command = ['timedatectl', 'set-timezone', timezone]
    action_utils.run(command, check=True)
