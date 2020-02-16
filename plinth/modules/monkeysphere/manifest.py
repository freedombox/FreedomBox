# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for monkeysphere.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup({
    'config': {
        'directories': ['/etc/monkeysphere/']
    },
    'secrets': {
        'directories': ['/var/lib/monkeysphere/']
    }
})
