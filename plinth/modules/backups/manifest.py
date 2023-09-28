# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for backups.
"""

# Currently, backup application does not have any settings. However, settings
# such as scheduler settings, backup location, secrets to connect to remove
# servers need to be backed up.
backup: dict = {}
