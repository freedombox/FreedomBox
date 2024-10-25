# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name':
        _('Mumble'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://wiki.mumble.info/wiki/Main_Page'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://wiki.mumble.info/wiki/Main_Page'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://wiki.mumble.info/wiki/Main_Page'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'mumble'
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://apps.apple.com/us/app/mumble/id443472808'
    }]
}, {
    'name':
        _('Mumblefly'),
    'platforms': [{
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://apps.apple.com/dk/app/mumblefy/id858752232'
    }]
}, {
    'name':
        _('Mumla'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'se.lublin.mumla')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'se.lublin.mumla')
    }]
}]

backup = {
    'config': {
        'files': ['/etc/mumble-server.ini']
    },
    'data': {
        'directories': ['/var/lib/mumble-server']
    },
    'services': ['mumble-server']
}

tags = [_('Audio chat'), _('Group conference'), _('Server')]
