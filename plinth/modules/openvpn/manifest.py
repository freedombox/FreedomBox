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
Application manifest for OpenVPN.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.clients import store_url, validate
from plinth.modules.backups.api import validate as validate_backup

_package_id = 'de.blinkt.openvpn'
_download_url = 'https://openvpn.net/community-downloads'

backup = validate_backup({'secrets': {'directories': ['/etc/openvpn/']}})

clients = validate([{
    'name':
        _('OpenVPN'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'openvpn',
    }, {
        'type': 'package',
        'format': 'brew',
        'name': 'openvpn',
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', _package_id)
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', _package_id)
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _download_url,
    }]
}, {
    'name':
        _('Tunnelblick'),
    'platforms': [{
        'type': 'download',
        'os': 'macos',
        'url': 'https://tunnelblick.net/downloads.html'
    }]
}])
