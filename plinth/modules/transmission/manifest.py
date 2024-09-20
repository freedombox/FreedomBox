# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name': _('Transmission'),
    'platforms': [{
        'type': 'web',
        'url': '/transmission'
    }]
}, {
    'name':
        _('Tremotesf'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'org.equeim.tremotesf')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'org.equeim.tremotesf')
    }]
}]

backup = {
    'data': {
        'directories': ['/var/lib/transmission-daemon/.config']
    },
    'secrets': {
        'files': ['/etc/transmission-daemon/settings.json']
    },
    'services': ['transmission-daemon']
}

tags = [_('File Sharing'), _('BitTorrent'), _('Client'), _('P2P')]
