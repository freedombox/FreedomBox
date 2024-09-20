# SPDX-License-Identifier: AGPL-3.0-or-later
"""App manifest for Tor Proxy."""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_ORBOT_PACKAGE_ID = 'org.torproject.android'
_TOR_BROWSER_DOWNLOAD_URL = \
    'https://www.torproject.org/download/download-easy.html'

clients = [{
    'name':
        _('Tor Browser'),
    'platforms': [{
        'type': 'download',
        'os': 'windows',
        'url': _TOR_BROWSER_DOWNLOAD_URL,
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _TOR_BROWSER_DOWNLOAD_URL,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _TOR_BROWSER_DOWNLOAD_URL,
    }]
}, {
    'name':
        _('Orbot: Proxy with Tor'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _ORBOT_PACKAGE_ID)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _ORBOT_PACKAGE_ID)
    }]
}]

backup = {
    'config': {
        'directories': ['/etc/tor/instances/fbxproxy/'],
    },
    'secrets': {
        'directories': ['/var/lib/tor-instances/fbxproxy/']
    },
    'services': ['tor@fbxproxy']
}

tags = [
    _('Proxy'),
    _('SOCKS5'),
    _('Anonymity Network'),
    _('Censorship Resistance'),
    _('Tor')
]
