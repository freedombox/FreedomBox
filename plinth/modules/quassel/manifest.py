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

from plinth.templatetags.plinth_extras import Desktop_OS, Mobile_OS, Store
from plinth.utils import play_store_url

quasseldroid_package_id = 'com.iskrembilen.quasseldroid',
quassel_download_url = 'http://quassel-irc.org/downloads'

clients = [{
    'name':
        _('Quassel'),
    'platforms': [{
        'type': 'download',
        'os': Desktop_OS.MAC_OS.value,
        'url': quassel_download_url,
    }, {
        'type': 'package',
        'os': 'Debian',
        'package_name': 'quassel-client',
    }]
}, {
    'name':
        _('Quassseldroid'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': play_store_url(quasseldroid_package_id),
    }]
}]
