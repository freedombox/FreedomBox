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
                'store_name': 'google_play_store',
                'fully_qualified_name': 'im.vector.alpha',
                'url': 'https://play.google.com/store/apps/details?id=im'
                       '.vector.alpha '
            },
            {
                'type': 'store',
                'os': 'Android',
                'os_version': '>=6.0',
                'store_name': 'fdroid_store',
                'fully_qualified_name': 'im.vector.alpha',
                'url': 'https://f-droid.org/packages/im.vector.alpha/'
            },
            {
                'type': 'web',
                'url': 'https://riot.im/app/#/home'
            },
            {
                'type': 'download',
                'os': 'Debian',
                'url': 'https://riot.im/desktop.html'
            },
            {
                'type': 'download',
                'os': 'macOS',
                'url': 'https://riot.im/desktop.html'
            },
            {
                'type': 'download',
                'os': 'Windows',
                'os_version': '>=7',
                'url': 'https://riot.im/desktop.html'
            },
        ]
    }]
