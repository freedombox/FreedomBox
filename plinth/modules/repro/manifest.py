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
        'name': _('Jitsi Meet'),
        'description': _('Jitsi is a set of open-source projects that allows '
                         'you to easily build and deploy secure '
                         'videoconferencing solutions. At the heart of Jitsi '
                         'are Jitsi Videobridge and Jitsi Meet, which let you '
                         'have conferences on the internet, while other '
                         'projects in the community enable other features '
                         'such as audio, dial-in, recording, '
                         'and simulcasting.'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'google_play_store',
                'fully_qualified_name': 'org.jitsi.meet',
                'url': 'https://play.google.com/store/apps/details?id=org'
                       '.jitsi.meet '
            },
            {
                'type': 'store',
                'os': 'iOS',
                'store_name': 'apple_store',
                'url': 'https://itunes.apple.com/in/app/jitsi-meet/id1165103905'
            },
            {
                'type': 'download',
                'os': 'Linux',
                'url': 'https://download.jitsi.org/jitsi/debian/'
            },
            {
                'type': 'dnf',
                'os': 'Linux',
                'package_name': 'jitsi'
            },
            {
                'type': 'download',
                'os': 'macOS',
                'url': 'https://download.jitsi.org/jitsi/macosx/jitsi-latest'
                       '.dmg '
            },
            {
                'type': 'download',
                'os': 'Windows',
                'url': 'https://download.jitsi.org/jitsi/windows/jitsi-latest'
                       '-x86.exe '
            },
            {
                'type': 'download',
                'os': 'macOS',
                'url': 'https://download.jitsi.org/jitsi/macosx/jitsi-latest'
                       '.dmg '
            }
        ]
    },
    {
        'name': _('CSipSimple'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'google_play_store',
                'fully_qualified_name': 'com.csipsimple',
                'url': 'https://play.google.com/store/apps/details?id=com'
                       '.csipsimple '
            }
        ]
    }
]
