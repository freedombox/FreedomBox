# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for pagekite.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup({
    'config': {
        'directories': ['/etc/pagekite.d/']
    },
    'services': ['pagekite']
})
