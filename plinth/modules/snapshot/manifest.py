# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for snapshot.
"""

backup = {
    'config': {
        'files': ['/etc/snapper/configs/root', '/etc/default/snapper']
    }
}
