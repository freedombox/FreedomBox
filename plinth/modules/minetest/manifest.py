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
        'name': _('Minetest'),
        'platforms': [
            {
                'type': 'download',
                'os': 'Windows(64-bit)',
                'os_version': 'XP, Vista, >=7',
                'url': 'https://github.com/minetest/minetest/releases'
                       '/download/0.4.16/minetest-0.4.16-win64.zip '
            },
            {
                'type': 'store',
                'os': 'Android',
                'store_type': 'google_play_store',
                'fully_qualified_name': 'net.minetest.minetest',
                'url': 'https://play.google.com/store/apps/details?id=net'
                       '.minetest.minetest '
            },
            {
                'type': 'store',
                'os': 'Android',
                'store_type': 'fdroid_store',
                'fully_qualified_name': 'net.minetest.minetest',
                'url': 'https://f-droid.org/packages/net.minetest.minetest/ '
            },
            {
                'type': 'apt',
                'os': 'Debian',
                'package_name': 'minetest'
            }
        ]
    }
]
