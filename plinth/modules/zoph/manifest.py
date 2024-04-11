# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Zoph'),
    'platforms': [{
        'type': 'web',
        'url': '/zoph/',
    }]
}]

backup = {
    'data': {
        'files': ['/var/lib/plinth/backups-data/zoph-database.sql'],
        'directories': ['/var/lib/zoph/']
    },
    'secrets': {
        'files': [
            '/etc/zoph.ini',
            '/etc/dbconfig-common/zoph.conf',
        ],
    }
}
