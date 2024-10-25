# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for OpenVPN.
"""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_package_id = 'de.blinkt.openvpn'
_download_url = 'https://openvpn.net/community-downloads'

backup = {'secrets': {'directories': ['/etc/openvpn/']}}

clients = [{
    'name':
        _('OpenVPN'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'openvpn',
    }, {
        'type': 'package',
        'format': 'brew',
        'name': 'openvpn',
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _package_id)
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://apps.apple.com/app/openvpn-connect/id590379981'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _download_url,
    }]
}, {
    'name':
        _('Tunnelblick'),
    'platforms': [{
        'type': 'download',
        'os': 'macos',
        'url': 'https://tunnelblick.net/downloads.html'
    }]
}]

tags = [_('VPN server'), _('Privacy'), _('Remote access')]
