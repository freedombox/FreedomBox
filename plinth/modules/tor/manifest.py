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
from plinth.modules.backups.api import validate as validate_backup

_orbot_package_id = 'org.torproject.android'
_tor_browser_download_url = \
    'https://www.torproject.org/download/download-easy.html'

clients = validate([{
    'name':
        _('Tor Browser'),
    'platforms': [{
        'type': 'download',
        'os': 'windows',
        'url': _tor_browser_download_url,
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _tor_browser_download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _tor_browser_download_url,
    }]
}, {
    'name':
        _('Orbot: Proxy with Tor'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _orbot_package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _orbot_package_id)
    }]
}])

backup = validate_backup({
    'config': {
        'directories': ['/etc/tor/']
    },
    'secrets': {
        'directories': ['/var/lib/tor/', '/var/lib/tor-instances/']
    },
    'services': ['tor@service']
})
