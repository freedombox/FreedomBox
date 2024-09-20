# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for email.
"""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [
    {
        'name': _('Roundcube'),
        'platforms': [{
            'type': 'web',
            'url': '/roundcube/'
        }]
    },
    {
        'name':
            _('Thunderbird'),
        'platforms': [{
            'type': 'download',
            'os': 'gnu-linux',
            'url': 'https://www.thunderbird.net/'
        }, {
            'type': 'download',
            'os': 'macos',
            'url': 'https://www.thunderbird.net/'
        }, {
            'type': 'download',
            'os': 'windows',
            'url': 'https://www.thunderbird.net/'
        }]
    },
    {
        'name':
            _('K-9 Mail'),
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
    },
    {
        'name':
            _('FairEmail'),
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
    },
]

backup = {
    'data': {
        'files': ['/etc/aliases', ],
        'directories': [
            '/etc/postfix/',
            '/etc/dovecot/conf.d/',
            '/etc/rspamd/',
            '/var/lib/postfix/freedombox-aliases/',
            '/var/lib/rspamd/',
            '/var/mail/',
        ]
    },
    'services': ['postfix', 'dovecot', 'rspamd']
}

tags = [_('Email')]
