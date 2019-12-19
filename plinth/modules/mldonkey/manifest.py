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
Application manifest for mldonkey.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.clients import store_url, validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name': _('MLDonkey'),
    'platforms': [{
        'type': 'web',
        'url': '/mldonkey/'
    }]
}, {
    'name':
        _('KMLDonkey'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://www.kde.org/applications/internet/kmldonkey/'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'kmldonkey',
    }]
}, {
    'name':
        _('AMLDonkey'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.devwom.amldonkey'),
    }]
}])

backup = validate_backup({
    'config': {
        'files': [
            '/var/lib/mldonkey/bittorrent.ini', '/var/lib/mldonkey/bt_dht.ini',
            '/var/lib/mldonkey/directconnect.ini',
            '/var/lib/mldonkey/donkey.ini', '/var/lib/mldonkey/downloads.ini',
            '/var/lib/mldonkey/files.ini',
            '/var/lib/mldonkey/file_sources.ini',
            '/var/lib/mldonkey/fileTP.ini', '/var/lib/mldonkey/friends.ini',
            '/var/lib/mldonkey/searches.ini', '/var/lib/mldonkey/servers.ini',
            '/var/lib/mldonkey/shared_files.ini',
            '/var/lib/mldonkey/shared_files_new.ini',
            '/var/lib/mldonkey/statistics.ini',
            '/var/lib/mldonkey/stats_bt.ini', '/var/lib/mldonkey/stats.ini',
            '/var/lib/mldonkey/stats_mod.ini', '/var/lib/mldonkey/users.ini'
        ]
    },
    'services': ['mldonkey-server']
})
