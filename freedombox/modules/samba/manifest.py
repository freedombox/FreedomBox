# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Samba.
"""

from django.utils.translation import gettext_lazy as _

from plinth.clients import store_url

clients = [{
    'name':
        _('SambaLite'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'de.schliweb.sambalite')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'de.schliweb.sambalite')
    }]
}, {
    'name':
        _('Ghost Commander'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.ghostsq.commander')
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
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://apps.apple.com/app/apple-store/id650377962'
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

backup: dict = {}

tags = [
    _('File sharing'),
    _('Local network'),
    _('Network drive'),
    _('Media storage'),
    _('Backup storage')
]
