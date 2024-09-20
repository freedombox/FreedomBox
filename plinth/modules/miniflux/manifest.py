# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for miniflux."""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [
    {
        'name': _('Miniflux'),
        'platforms': [{
            'type': 'web',
            'url': '/miniflux/'
        }]
    },
    {
        'name':
            _('Fluent Reader Lite'),
        'platforms': [{
            'type': 'store',
            'os': 'android',
            'store_name': 'google-play',
            'url': store_url('google-play', 'me.hyliu.fluent_reader_lite'),
        }, {
            'type': 'store',
            'os': 'ios',
            'store_name': 'app-store',
            'url': 'https://apps.apple.com/app/id1549611796',
        }]
    },
    {
        'name':
            _('Fluent Reader'),
        'platforms': [{
            'type': 'download',
            'os': 'windows',
            'url': 'https://github.com/yang991178/fluent-reader/releases',
        }, {
            'type': 'download',
            'os': 'macos',
            'url': 'https://github.com/yang991178/fluent-reader/releases',
        }]
    },
    {
        'name':
            _('FluxNews'),
        'platforms': [{
            'type': 'store',
            'os': 'android',
            'store_name': 'f-droid',
            'url': store_url('f-droid', 'de.circle_dev.flux_news')
        }, {
            'type': 'store',
            'os': 'android',
            'store_name': 'google-play',
            'url': store_url('google-play', 'de.circle_dev.flux_news')
        }]
    },
    {
        'name':
            _('MiniFlutt'),
        'platforms': [{
            'type': 'store',
            'os': 'android',
            'store_name': 'google-play',
            'url': store_url('google-play', 'be.martinelli.miniflutt')
        }]
    },
    {
        'name':
            _('NetNewsWire'),
        'platforms': [{
            'type': 'download',
            'os': 'macos',
            'url': 'https://netnewswire.com/',
        }, {
            'type': 'store',
            'os': 'ios',
            'store_name': 'app-store',
            'url': 'https://apps.apple.com/us/app/'
                   'netnewswire-rss-reader/id1480640210',
        }]
    },
    {
        'name':
            _('Newsflash'),
        'platforms': [{
            'type': 'download',
            'os': 'gnu-linux',
            'url': 'https://flathub.org/apps/details/'
                   'io.gitlab.news_flash.NewsFlash'
        }]
    },
    {
        'name':
            _('Read You'),
        'platforms': [{
            'type': 'store',
            'os': 'android',
            'store_name': 'f-droid',
            'url': store_url('f-droid', 'me.ash.reader')
        }]
    },
    {
        'name':
            _('RSS Guard'),
        'platforms': [{
            'type': 'download',
            'os': 'gnu-linux',
            'url': 'https://github.com/martinrotter/rssguard/releases',
        }, {
            'type': 'download',
            'os': 'macos',
            'url': 'https://github.com/martinrotter/rssguard/releases',
        }, {
            'type': 'download',
            'os': 'windows',
            'url': 'https://github.com/martinrotter/rssguard/releases',
        }]
    },
]

backup = {
    'config': {
        'files': [
            '/etc/miniflux/freedombox.conf',
            '/var/lib/plinth/backups-data/miniflux-database.sql',
        ],
    },
    'secrets': {
        'files': [
            '/etc/miniflux/database', '/etc/dbconfig-common/miniflux.conf'
        ]
    },
    'services': ['miniflux']
}

tags = [_('Feed Reader'), _('News'), _('RSS'), _('ATOM')]
