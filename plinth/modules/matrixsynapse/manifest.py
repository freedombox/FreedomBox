# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.modules.backups.api import validate as validate_backup
from plinth.clients import store_url, validate

_android_package_id = 'im.vector.alpha'
_riot_desktop_download_url = 'https://riot.im/desktop.html'

clients = validate([{
    'name':
        _('Riot'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _android_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _android_package_id)
    }, {
        'type': 'web',
        'url': 'https://riot.im/app/#/home'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _riot_desktop_download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _riot_desktop_download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _riot_desktop_download_url,
    }]
}])

backup = validate_backup({
    'config': {
        'directories': ['/etc/matrix-synapse/conf.d/'],
        'files': [
            '/etc/matrix-synapse/homeserver.yaml',
            '/etc/matrix-synapse/log.yaml'
        ]
    },
    'data': {
        'directories': [
            '/var/lib/matrix-synapse/media/',
            '/var/lib/matrix-synapse/uploads/'
        ],
        'files': ['/var/lib/matrix-synapse/homeserver.db']
    },
    'secrets': {
        'files': [
            '/etc/matrix-synapse/homeserver.signing.key',
            '/etc/matrix-synapse/homeserver.tls.crt',
            '/etc/matrix-synapse/homeserver.tls.dh',
            '/etc/matrix-synapse/homeserver.tls.key'
        ]
    },
    'services': ['matrix-synapse']
})
