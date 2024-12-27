# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

from . import privileged

clients = [
    {
        'name': _('SOGo'),
        'platforms': [{
            'type': 'web',
            'url': '/SOGo/'
        }]
    },
    {
        'name':
            _('Thunderbird + SOGo connector'),
        'platforms': [{
            'type': 'download',
            'os': 'gnu-linux',
            'url': 'https://www.sogo.nu/download.html#/frontends'
        }, {
            'type': 'download',
            'os': 'macos',
            'url': 'https://www.sogo.nu/download.html#/frontends'
        }, {
            'type': 'download',
            'os': 'windows',
            'url': 'https://www.sogo.nu/download.html#/frontends'
        }]
    },
    {
        'name':
            _('DAVx5'),
        'platforms': [{
            'type': 'store',
            'os': 'android',
            'store_name': 'f-droid',
            'url': store_url('f-droid', 'at.bitfire.davdroid'),
        }, {
            'type': 'store',
            'os': 'android',
            'store_name': 'google-play',
            'url': store_url('google-play', 'at.bitfire.davdroid'),
        }]
    },
    {
        'name':
            _('GNOME Calendar'),
        'platforms': [{
            'type': 'package',
            'format': 'deb',
            'name': 'gnome-calendar'
        }]
    },
]

backup = {
    'data': {
        'files': [str(privileged.DB_BACKUP_FILE)],
    },
    'services': ['sogo'],
    'secrets': {
        'directories': [str(privileged.CONFIG_FILE)]
    },
}

tags = [
    _('Webmail'),
    _('Groupware'),
    _('Calender'),
    _('Address book'),
    _('CalDAV'),
    _('CardDAV')
]
