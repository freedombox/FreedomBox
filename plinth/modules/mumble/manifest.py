#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.utils.translation import ugettext_lazy as _

clients = [{
    'name':
        _('Mumble'),
    'platforms': [{
        'type': 'download',
        'os': 'Windows',
        'arch': 'i386',
        'url': 'https://github.com/mumble-voip/mumble/releases'
               '/download/1.2.19/mumble-1.2.19.msi '
    }, {
        'type': 'download',
        'os': 'Windows(64-bit)',
        'arch': 'amd64',
        'url': 'https://dl.mumble.info/mumble-1.3.0~2569~gd196a4b'
               '~snapshot.winx64.msi '
    }, {
        'type': 'download',
        'os': 'macOS',
        'url': 'https://github.com/mumble-voip/mumble/releases'
               '/download/1.2.19/Mumble-1.2.19.dmg '
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'mumble'
    }, {
        'type': 'store',
        'os': 'iOS',
        'os_version': '>=8.0',
        'store_name': 'apple_store',
        'url': 'https://itunes.apple.com/us/app/mumble/id443472808'
    }]
}, {
    'name':
        _('Plumble'),
    'platforms': [{
        'type': 'store',
        'os': 'Android',
        'store_name': 'google_play_store',
        'url': 'https://play.google.com/store/apps/details?id=com'
               '.morlunk.mumbleclient.free ',
        'fully_qualified_name': 'com.morlunk.mumbleclient'
    }, {
        'type': 'store',
        'os': 'Android',
        'store_name': 'fdroid_store',
        'url': 'https://play.google.com/store/apps/details?id=com'
               '.morlunk.mumbleclient.free ',
        'fully_qualified_name': 'com.morlunk.mumbleclient'
    }]
}, {
    'name':
        _('Mumblefly'),
    'platforms': [{
        'type': 'store',
        'os': 'iOS',
        'os_version': '>=7.0',
        'store_name': 'apple_store',
        'url': 'https://itunes.apple.com/dk/app/mumblefy/id858752232'
    }]
}]
