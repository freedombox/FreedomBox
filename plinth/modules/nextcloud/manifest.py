# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for Nextcloud."""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

_nextcloud_android_package_id = 'com.nextcloud.client'

clients = [{
    'name': _('Nextcloud'),
    'platforms': [{
        'type': 'web',
        'url': '/nextcloud/'
    }]
}, {
    'name':
        _('Nextcloud'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://nextcloud.com/install/#install-clients'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://nextcloud.com/install/#install-clients'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://nextcloud.com/install/#install-clients'
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://itunes.apple.com/us/app/nextcloud/id1125420102?mt=8'
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _nextcloud_android_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _nextcloud_android_package_id)
    }]
}]

backup = {
    'data': {
        'directories': [
            '/var/lib/containers/storage/volumes/nextcloud-volume-fbx/'
        ],
        'files': [
            '/var/lib/plinth/backups-data/nextcloud-database.sql',
            '/etc/redis/redis.conf'
        ]
    }
}
