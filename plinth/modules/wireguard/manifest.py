# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for WireGuard.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.clients import store_url, validate

_wireguard_package_id = 'com.wireguard.android'

clients = validate([{
    'name':
        _('WireGuard'),
    'platforms': [{
        'type':
            'download',
        'os':
            'windows',
        'url':
            'https://download.wireguard.com/windows-client/'
        'wireguard-amd64-0.0.23.msi'
    }, {
        'type':
            'download',
        'os':
            'macos',
        'url':
            'https://itunes.apple.com/us/app/wireguard/id1451685025?ls=1&mt=12'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'wireguard'
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _wireguard_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _wireguard_package_id)
    }, {
        'type':
            'store',
        'os':
            'ios',
        'store_name':
            'app-store',
        'url':
            'https://itunes.apple.com/us/app/wireguard/id1441195209?ls=1&mt=8'
    }]
}])
