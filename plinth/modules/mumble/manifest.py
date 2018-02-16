#
# This file is part of FreedomBox.
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

from plinth.clients import store_url, validate

_plumble_package_id = 'com.morlunk.mumbleclient'

clients = validate([{
    'name':
        _('Mumble'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://wiki.mumble.info/wiki/Main_Page'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://wiki.mumble.info/wiki/Main_Page'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://wiki.mumble.info/wiki/Main_Page'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'mumble'
    }, {
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://itunes.apple.com/us/app/mumble/id443472808'
    }]
}, {
    'name':
        _('Plumble'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _plumble_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _plumble_package_id)
    }]
}, {
    'name':
        _('Mumblefly'),
    'platforms': [{
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://itunes.apple.com/dk/app/mumblefy/id858752232'
    }]
}])
