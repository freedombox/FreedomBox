# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for upgrades.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup(
    {'config': {
        'files': ['/etc/apt/apt.conf.d/20auto-upgrades']
    }})
