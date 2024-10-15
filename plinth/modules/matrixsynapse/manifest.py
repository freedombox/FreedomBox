# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_element_android_package_id = 'im.vector.app'
_element_desktop_download_url = 'https://element.io/get-started'
_fluffychat_android_package_id = 'chat.fluffy.fluffychat'
_fluffychat_desktop_download_url = 'https://fluffychat.im/'

clients = [{
    'name':
        _('Element'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _element_android_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _element_android_package_id)
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://apps.apple.com/app/vector/id1083446067'
    }, {
        'type': 'web',
        'url': 'https://app.element.io/'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _element_desktop_download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _element_desktop_download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _element_desktop_download_url,
    }]
}, {
    'name':
        _('FluffyChat'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _fluffychat_android_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _fluffychat_android_package_id)
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://apps.apple.com/app/fluffychat/id1551469600'
    }, {
        'type': 'web',
        'url': 'https://fluffychat.im/web'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _fluffychat_desktop_download_url,
    }]
}]

backup = {
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
}

tags = [
    _('Chat room'),
    _('Encrypted messaging'),
    _('Audio chat'),
    _('Video chat'),
    _('Matrix server'),
]
