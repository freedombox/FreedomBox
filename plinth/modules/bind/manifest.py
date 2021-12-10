# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for bind.
"""

backup = {
    'config': {
        'files': ['/etc/bind/named.conf.options']
    },
    'services': ['named']
}
