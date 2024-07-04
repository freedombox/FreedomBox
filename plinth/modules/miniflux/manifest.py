# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for miniflux."""

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Miniflux'),
    'platforms': [{
        'type': 'web',
        'url': '/miniflux/'
    }]
}]

backup = {
    'config': {
        'files': [
            '/etc/miniflux/freedombox.conf',
            '/var/lib/plinth/backups-data/miniflux-database.sql',
        ],
    },
    'secrets': {
        'files': [
            '/etc/miniflux/database', '/etc/dbconfig-common/miniflux.conf'
        ]
    },
    'services': ['miniflux']
}
