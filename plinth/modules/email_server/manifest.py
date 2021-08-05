# SPDX-License-Identifier: AGPL-3.0-or-later
from django.utils.translation import ugettext_lazy as _
from plinth.clients import store_url

clients = [{
    'name': _('Roundcube'),
    'platforms': [{
        'type': 'web',
        'url': '/plinth/apps/roundcube'
    }]
}, {
    'name': _('Thunderbird'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://www.thunderbird.net/en-US/'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://www.thunderbird.net/en-US/'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://www.thunderbird.net/en-US/'
    }]
}, {
    'name': _('K-9 Mail'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.fsck.k9')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.fsck.k9')
    }]
}, {
    'name': _('FairEmail'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'eu.faircode.email')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'eu.faircode.email')
    }]
}]

backup = {
    'data': {
        'directories': [
            '/var/lib/plinth/mailsrv',
            '/var/spool/postfix/fbx-managed',
            '/etc/postfix',
            '/etc/dovecot',
            '/etc/rspamd',
            '/var/lib/rspamd',
        ]
    },
    'services': ['postfix', 'dovecot', 'rspamd']
}
