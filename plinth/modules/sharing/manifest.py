# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for sharing.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup({
    'config': {
        'files': ['/etc/apache2/conf-available/sharing-freedombox.conf']
    },
    'services': [{
        'type': 'apache',
        'kind': 'config',
        'name': 'sharing-freedombox'
    }]
})
