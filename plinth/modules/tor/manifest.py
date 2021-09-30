# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_orbot_package_id = 'org.torproject.android'
_tor_browser_download_url = \
    'https://www.torproject.org/download/download-easy.html'

clients = [{
    'name':
        _('Tor Browser'),
    'platforms': [{
        'type': 'download',
        'os': 'windows',
        'url': _tor_browser_download_url,
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _tor_browser_download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _tor_browser_download_url,
    }]
}, {
    'name':
        _('Orbot: Proxy with Tor'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _orbot_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _orbot_package_id)
    }]
}]

backup = {
    'config': {
        'directories': ['/etc/tor/']
    },
    'secrets': {
        'directories': ['/var/lib/tor/', '/var/lib/tor-instances/']
    },
    'services': ['tor@plinth']
}
