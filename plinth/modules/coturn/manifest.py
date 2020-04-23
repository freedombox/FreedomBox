# SPDX-License-Identifier: AGPL-3.0-or-later

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup({
    'secrets': {
        'directories': ['/etc/coturn']
    },
    'services': ['coturn']
})
