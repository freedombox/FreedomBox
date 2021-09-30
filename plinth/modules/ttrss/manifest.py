# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name':
        _('Tiny Tiny RSS (Fork)'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'org.fox.tttrss')
    }]
}, {
    'name':
        _('Tiny Tiny RSS'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'org.fox.ttrss')
    }, {
        'type': 'web',
        'url': '/tt-rss'
    }]
}]

backup = {
    'data': {
        'files': ['/var/lib/plinth/backups-data/ttrss-database.sql']
    },
    'secrets': {
        'files': ['/etc/tt-rss/database.php']
    },
    'services': ['tt-rss']
}
