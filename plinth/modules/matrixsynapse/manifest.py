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

clients = [
    {
        'name': _('Riot'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_type': 'google_play_store',
                'fully_qualified_name': 'im.vector.alpha',
                'url': 'https://play.google.com/store/apps/details?id=im'
                       '.vector.alpha '
            },
            {
                'type': 'store',
                'os': 'Android',
                'os_version': '>=6.0',
                'store_type': 'fdroid_store',
                'fully_qualified_name': 'im.vector.alpha',
                'url': 'https://f-droid.org/packages/im.vector.alpha/'
            },
            {
                'type': 'web',
                'url': 'https://riot.im/app/#/home'
            },
            {
                'type': 'download',
                'os': 'macOS',
                'url': 'https://riot.im/download/desktop/install/macos'
                            '/Riot-0.12.4.dmg'
            },
            {
                'type': 'download',
                'os': 'Windows(32 bit)',
                'os_version': '>=7',
                'url': 'https://riot.im/download/desktop/install/win32/ia32/'
                       'Riot%20Setup%200.12.4-ia32.exe'
            },
            {
                'type': 'download',
                'os': 'Windows(64 bit)',
                'os_version': '>=7',
                'url': 'https://riot.im/download/desktop/install/win32/x64/Riot'
                       '%20Setup%200.12.4.exe'
            },
            {
                'type': 'download',
                'os': 'Debian/Ubuntu',
                'url': 'https://riot.im/packages/debian/'
            }
        ]
    }]
