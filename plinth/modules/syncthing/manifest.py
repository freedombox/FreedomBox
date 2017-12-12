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

from plinth.clients import store_url, validate

_package_id = 'com.nutomic.syncthingandroid'
_download_url = 'https://syncthing.net/'

clients = validate([{
    'name':
        _('Syncthing'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'syncthing',
    }, {
        'type': 'package',
        'format': 'brew',
        'name': 'syncthing',
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _download_url,
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _package_id)
    }, {
        'type': 'web',
        'url': '/syncthing'
    }]
}])
