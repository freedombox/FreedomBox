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

clients = validate([{
    'name':
        _('Quassel'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'http://quassel-irc.org/downloads'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'http://quassel-irc.org/downloads'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'http://quassel-irc.org/downloads'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'quassel-client',
    }, {
        'type': 'package',
        'format': 'brew',
        'name': 'quassel-client',
    }]
}, {
    'name':
        _('Quasseldroid'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.iskrembilen.quasseldroid'),
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.iskrembilen.quasseldroid'),
    }]
}])
