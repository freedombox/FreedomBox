# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for pagekite.
"""

backup = {
    'config': {
        'directories': ['/etc/pagekite.d/']
    },
    'services': ['pagekite']
}
