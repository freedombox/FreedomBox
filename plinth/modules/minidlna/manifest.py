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

from plinth.modules.backups.api import validate as validate_backup
from plinth.clients import validate, store_url

clients = validate([
    {
        'name': _('vlc'),
        'platforms': [
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'deb',
                'name': 'vlc',
            },
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'rpm',
                'name': 'vlc',
            },
            {
                'type': 'download',
                'os': 'windows',
                'url': 'https://www.videolan.org/vlc/download-windows.html',
            },
            {
                'type': 'download',
                'os': 'macos',
                'url': 'https://www.videolan.org/vlc/download-macosx.html',
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'google-play',
                'url': store_url('google-play', 'org.videolan.vlc')
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'f-droid',
                'url': store_url('f-droid', 'org.videolan.vlc')
            },
        ]
    },
    {
        'name': _('kodi'),
        'platforms': [
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'deb',
                'name': 'kodi',
            },
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'rpm',
                'name': 'kodi',
            },
            {
                'type': 'download',
                'os': 'windows',
                'url': 'http://kodi.tv/download/',
            },
            {
                'type': 'download',
                'os': 'macos',
                'url': 'http://kodi.tv/download/',
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'google-play',
                'url': store_url('google-play', 'org.xbmc.kodi')
            },
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'f-droid',
                'url': store_url('f-droid', 'org.xbmc.kodi')
            },
        ]
    },
    {
        'name': _('yaacc'),
        'platforms': [
            {
                'type': 'store',
                'os': 'android',
                'store_name': 'f-droid',
                'url': store_url('f-droid', 'de.yaacc')
            },
        ]
    },
    {
        'name': _('totem'),
        'platforms': [
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'deb',
                'name': 'totem',
            },
            {
                'type': 'package',
                'os': 'gnu-linux',
                'format': 'rpm',
                'name': 'totem',
            },
        ]
    },
])

# TODO: get all media directories from config file
# for now hard code default media folder.
backup = validate_backup({
    'data': {
        'directories': ['/var/lib/minidlna']
    }
})
