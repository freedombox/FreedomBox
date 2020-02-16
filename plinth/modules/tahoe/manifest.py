# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for tahoe-lafs.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup({
    'secrets': {
        'directories': ['/var/lib/tahoe-lafs/']
    },
    'services': ['tahoe-lafs']
})
