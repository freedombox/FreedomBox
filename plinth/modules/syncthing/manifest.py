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

metadata = {
    'syncthing': {
        'version': '0.14.39',
        'android-package-id': 'com.nutomic.syncthingandroid',
    },
}

clients = [{
    'name':
        _('Syncthing'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'syncthing',
    }, {
        'type': 'package',
        'format': 'homebrew',
        'name': 'syncthing',
    }, {
        'type':
            'download',
        'os':
            'all',
        'url':
            'https://github.com/syncthing/syncthing/releases/tag/v{}'
            .format(metadata['syncthing']['version'])
    }, {
        'type': 'download',
        'os': Desktop_OS.GNU_LINUX.value,
        'arch': 'amd64',
        'url': 'https://github.com/syncthing/syncthing/releases/'
               'download/v{0}/syncthing-linux-amd64-v{0}.tar.gz'
               .format(metadata['syncthing']['version']),
    }, {
        'type': 'download',
        'os': Desktop_OS.MAC_OS.value,
        'arch': 'amd64',
        'url': 'https://github.com/syncthing/syncthing/releases/'
               'download/v{0}/syncthing-macosx-amd64-v{0}.tar.gz'
               .format(metadata['syncthing']['version']),
    }, {
        'type': 'download',
        'os': Desktop_OS.WINDOWS.value,
        'arch': 'amd64',
        'url': 'https://github.com/syncthing/syncthing/releases/'
               'download/v{0}/syncthing-windows-amd64-v{0}.zip'
               .format(metadata['syncthing']['version']),
    }, {
        'type':
            'store',
        'os':
            Mobile_OS.ANDROID.value,
        'store_name':
            Store.GOOGLE_PLAY.value,
        'fully_qualified_name':
            'com.nutomic.syncthingandroid',
        'url':
            'https://play.google.com/store/apps/details?id={}'
            .format(metadata['syncthing']['android-package-id'])
    }, {
        'type':
            'store',
        'os':
            Mobile_OS.ANDROID.value,
        'store_name':
            Store.F_DROID.value,
        'fully_qualified_name':
            'com.nutomic.syncthingandroid',
        'url':
            'https://f-droid.org/packages/{}'
            .format(metadata['syncthing']['android-package-id'])
    }, {
        'type': 'web',
        'relative_url': '/syncthing'
    }]
}]
