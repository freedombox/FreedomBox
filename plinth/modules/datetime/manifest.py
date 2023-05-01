# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for datetime.
"""

backup = {
    'data': {
        'files': ['/etc/localtime']
    },
    'services': ['systemd-timedated'],
}
