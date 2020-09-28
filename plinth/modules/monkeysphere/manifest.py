# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for monkeysphere.
"""

backup = {
    'config': {
        'directories': ['/etc/monkeysphere/']
    },
    'secrets': {
        'directories': ['/var/lib/monkeysphere/']
    }
}
