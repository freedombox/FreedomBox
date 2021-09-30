# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Samba.
"""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

SHARES_CONF_BACKUP_FILE = '/var/lib/plinth/backups-data/samba-shares-dump.conf'

clients = [{
    'name':
        _('Android Samba Client'),
    'platforms': [{
        'type':
            'store',
        'os':
            'android',
        'store_name':
            'f-droid',
        'url':
            store_url('f-droid', 'com.google.android.sambadocumentsprovider')
    }]
}, {
    'name':
        _('Ghost Commander - Samba plugin'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.ghostsq.commander.samba')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.ghostsq.commander.smb')
    }]
}, {
    'name':
        _('VLC media player'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'org.videolan.vlc')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'org.videolan.vlc')
    }]
}, {
    'name':
        _('GNOME Files'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'nautilus',
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://wiki.gnome.org/Apps/Files'
    }]
}, {
    'name':
        _('Dolphin'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'dolphin',
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://kde.org/applications/system/org.kde.dolphin'
    }]
}]

backup = {
    'data': {
        'files': [SHARES_CONF_BACKUP_FILE]
    },
    'services': ['smbd', 'nmbd']
}
