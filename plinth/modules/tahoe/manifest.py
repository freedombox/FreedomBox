# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manfiest for tahoe-lafs.
"""

backup = {
    'secrets': {
        'directories': ['/var/lib/tahoe-lafs/']
    },
    'services': ['tahoe-lafs']
}
