# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for shadowsocks.
"""

from plinth.modules.backups.api import validate as validate_backup

backup = validate_backup({
    'secrets': {
        'files': ['/etc/shadowsocks-libev/freedombox.json']
    },
    'services': ['shadowsocks-libev-local@freedombox']
})
