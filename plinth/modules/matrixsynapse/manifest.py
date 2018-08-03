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

_android_package_id = 'im.vector.alpha'
_riot_desktop_download_url = 'https://riot.im/desktop.html'

clients = validate([{
    'name':
        _('Riot'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _android_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _android_package_id)
    }, {
        'type': 'web',
        'url': 'https://riot.im/app/#/home'
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _riot_desktop_download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _riot_desktop_download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _riot_desktop_download_url,
    }]
}])

backup = {
    'config': {
        'directories': ['/etc/matrix-synapse/conf.d/'],
        'files': [
            '/etc/matrix-synapse/homeserver.yaml',
            '/etc/matrix-synapse/log.yaml'
        ],
    },
    'data': {
        'directories': [
            '/var/lib/matrix-synapse/media/',
            '/var/lib/matrix-synapse/uploads/'
        ],
        'files': ['/var/lib/matrix-synapse/homeserver.db'],
    },
    'secrets': {
        'directories': [],
        'files': [
            '/etc/matrix-synapse/homeserver.signing.key',
            '/etc/matrix-synapse/homeserver.tls.crt',
            '/etc/matrix-synapse/homeserver.tls.dh',
            '/etc/matrix-synapse/homeserver.tls.key'
        ],
    },
    'services': ['matrix-synapse']
}
