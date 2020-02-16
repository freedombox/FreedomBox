# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for security.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup(
    {'config': {
        'files': ['/etc/security/access.d/50freedombox.conf']
    }})
