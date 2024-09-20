# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_package_id = 'com.nutomic.syncthingandroid'
_download_url = 'https://syncthing.net/'

clients = [{
    'name':
        _('Syncthing'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'syncthing',
    }, {
        'type': 'package',
        'format': 'brew',
        'name': 'syncthing',
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _download_url,
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _package_id)
    }, {
        'type': 'web',
        'url': '/syncthing'
    }]
}]

backup = {
    'secrets': {
        'directories': [
            '/var/lib/syncthing/.config', '/var/lib/syncthing/.local'
        ]
    },
    'services': ['syncthing@syncthing']
}

tags = [_('Synchronization'), _('File Sharing'), _('Cloud Storage')]
