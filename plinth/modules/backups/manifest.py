# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for backups.
"""

from plinth.modules.backups.api import validate as validate_backup

# Currently, backup application does not have any settings. However, settings
# such as scheduler settings, backup location, secrets to connect to remove
# servers need to be backed up.
backup = validate_backup({})
