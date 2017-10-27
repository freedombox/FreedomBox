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
        'name': _('TT-RSS Reader'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'google_play-store',
                'url': 'https://play.google.com/store/apps/details?id=org'
                       '.ttrssreader',
                'fully_qualified_name': 'org.ttrssreader'
            },
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'fdroid_store',
                'url': 'https://f-droid.org/packages/org.ttrssreader/',
                'fully_qualified_name': 'org.ttrssreader'
            },
            {
                'type': 'web',
                'relative_url': '/tt-rss'
            }
        ]
    }
]
