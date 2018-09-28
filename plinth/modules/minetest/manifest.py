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

from plinth.modules.backups.backups import validate as validate_backup
from plinth.clients import store_url, validate

clients = validate([{
    'name':
        _('Minetest'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://www.minetest.net/downloads/'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://www.minetest.net/downloads/'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://www.minetest.net/downloads/'
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'net.minetest.minetest')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'net.minetest.minetest')
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'minetest'
    }]
}])

backup = validate_backup({
    'config': {
        'files': ['/etc/minetest/minetest.conf']
    },
    'data': {
        'directories': ['/var/games/minetest-server/']
    },
    'services': ['minetest-server']
})
