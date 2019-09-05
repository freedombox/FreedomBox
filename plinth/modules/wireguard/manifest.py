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
"""
Application manifest for WireGuard.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.clients import store_url, validate

_wireguard_package_id = 'com.wireguard.android'

clients = validate([{
    'name':
        _('WireGuard'),
    'platforms': [{
        'type':
            'download',
        'os':
            'windows',
        'url':
            'https://download.wireguard.com/windows-client/'
        'wireguard-amd64-0.0.23.msi'
    }, {
        'type':
            'download',
        'os':
            'macos',
        'url':
            'https://itunes.apple.com/us/app/wireguard/id1451685025?ls=1&mt=12'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'wireguard'
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _wireguard_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _wireguard_package_id)
    }, {
        'type':
            'store',
        'os':
            'ios',
        'store_name':
            'app-store',
        'url':
            'https://itunes.apple.com/us/app/wireguard/id1441195209?ls=1&mt=8'
    }]
}])
