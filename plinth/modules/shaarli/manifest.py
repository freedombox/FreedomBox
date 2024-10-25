# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Shaarli.
"""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name':
        _('Shaarlier'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.dimtion.shaarlier'),
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.dimtion.shaarlier'),
    }]
}, {
    'name': _('Shaarli'),
    'platforms': [{
        'type': 'web',
        'url': '/shaarli/'
    }]
}]

backup = {'data': {'directories': ['/var/lib/shaarli/data']}}

tags = [_('Bookmarks'), _('Link blog'), _('Single user')]
