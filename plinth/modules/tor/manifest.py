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

version = '7.0.6'

clients = [{
    'name':
        _('Tor Browser'),
    'platforms': [{
        'type': 'download',
        'os': Desktop_OS.WINDOWS.value,
        'os_version': 'Windows XP, Vista, >=7',
        'url': 'https://www.torproject.org/dist/torbrowser/{v}'
               '/torbrowser-install-{v}_en-US.exe '.format(v=version)
    }, {
        'type': 'download',
        'os': Desktop_OS.GNU_LINUX.value,
        'url': 'https://www.torproject.org/dist/torbrowser/{v}/tor'
               '-browser-linux64-{v} _en-US.tar.xz'.format(v=version)
    }, {
        'type': 'download',
        'os': Desktop_OS.MAC_OS.value,
        'arch': 'amd64',
        'url': 'https://www.torproject.org/dist/torbrowser/{v}'
               '/TorBrowser-{v}-osx64_en-US.dmg'.format(v=version)
    }]
}, {
    'name':
        _('Orbot: Proxy with Tor'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': 'https://play.google.com/store/apps/details?id=org'
               '.torproject.android',
        'fully_qualified_name': 'org.torproject.android'
    }, {
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.F_DROID.value,
        'url': 'https://play.google.com/store/apps/details?id=org'
               '.torproject.android',
        'fully_qualified_name': 'org.torproject.android'
    }]
}]
