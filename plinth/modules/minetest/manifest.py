# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name':
        _('Luanti'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://www.luanti.org/downloads/'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://www.luanti.org/downloads/'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://www.luanti.org/downloads/'
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'net.minetest.minetest')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'net.minetest.minetest')
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'luanti'
    }]
}]

backup = {
    'config': {
        'files': ['/etc/minetest/minetest.conf']
    },
    'data': {
        'directories': ['/var/games/minetest-server/']
    },
    'services': ['minetest-server']
}

tags = [_('Game server'), _('Block sandbox'), _('Platform')]
