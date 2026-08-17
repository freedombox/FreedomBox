# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for Home Assistant."""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_android_package_id = 'io.homeassistant.companion.android'

clients = [
    {
        'name': _('Home Assistant'),
        'platforms': [{
            'type': 'web',
            'url': '#'  # Filled in later
        }]
    },
    {
        'name':
            _('Home Assistant'),
        'platforms': [{
            'type': 'download',
            'os': 'macos',
            'url': 'https://apps.apple.com/us/app/home-assistant/id1099568401'
        }, {
            'type': 'store',
            'os': 'ios',
            'store_name': 'app-store',
            'url': 'https://apps.apple.com/us/app/home-assistant/id1099568401'
                   '?platform=iphone'
        }, {
            'type':
                'store',
            'os':
                'android',
            'store_name':
                'google-play',
            'url':
                store_url('google-play', 'io.homeassistant.companion.android')
        }, {
            'type':
                'store',
            'os':
                'android',
            'store_name':
                'f-droid',
            'url':
                store_url('f-droid',
                          'io.homeassistant.companion.android.minimal')
        }]
    }
]

backup = {
    'data': {
        'directories': ['/var/lib/home-assistant-freedombox/']
    },
    'services': ['home-assistant-freedombox']
}

tags = [
    _('Home Automation'),
    _('IoT'),
    _('Wi-Fi'),
    _('ZigBee'),
    _('Z-Wave'),
    _('Thread')
]
