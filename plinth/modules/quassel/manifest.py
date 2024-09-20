# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name':
        _('Quassel'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'http://quassel-irc.org/downloads'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'http://quassel-irc.org/downloads'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'http://quassel-irc.org/downloads'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'quassel-client',
    }, {
        'type': 'package',
        'format': 'brew',
        'name': 'quassel-client',
    }]
}, {
    'name':
        _('Quasseldroid'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.iskrembilen.quasseldroid'),
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.iskrembilen.quasseldroid'),
    }]
}]

backup = {
    'secrets': {
        'directories': ['/var/lib/quassel/']
    },
    'services': ['quasselcore'],
}

tags = [_('Chat Room'), _('IRC'), _('Client')]
