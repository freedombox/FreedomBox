# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Samba.
"""

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

SHARES_CONF_BACKUP_FILE = '/var/lib/plinth/backups-data/samba-shares-dump.conf'

clients = validate([])

backup = validate_backup({
    'data': {
        'files': [SHARES_CONF_BACKUP_FILE]
    },
    'services': ['smbd', 'nmbd']
})
