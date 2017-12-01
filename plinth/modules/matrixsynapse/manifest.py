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
from plinth.utils import f_droid_url, play_store_url

android_package_id = 'im.vector.alpha'
riot_desktop_download_url = 'https://riot.im/desktop.html'

clients = [{
    'name':
        _('Riot'),
    'platforms': [
        {
            'type': 'store',
            'os': Mobile_OS.ANDROID.value,
            'store_name': Store.GOOGLE_PLAY.value,
            'url': play_store_url(android_package_id)
        },
        {
            'type': 'store',
            'os': Mobile_OS.ANDROID.value,
            'store_name': Store.F_DROID.value,
            'url': f_droid_url(android_package_id)
        },
        {
            'type': 'web',
            'url': 'https://riot.im/app/#/home'
        },
        {
            'type': 'download',
            'os': Desktop_OS.GNU_LINUX.value,
            'url': riot_desktop_download_url,
        },
        {
            'type': 'download',
            'os': Desktop_OS.MAC_OS.value,
            'url': riot_desktop_download_url,
        },
        {
            'type': 'download',
            'os': Desktop_OS.WINDOWS.value,
            'url': riot_desktop_download_url,
        },
    ]
}]
