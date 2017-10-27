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

from plinth.modules.jsxc import manifest as jsxc_manifest

clients = [
    {
        'name': _('yaxim'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'google_play_store',
                'fully_qualified_name': 'org.yaxim.androidclient',
                'url': 'https://play.google.com/store/apps/details?id=org'
                       '.yaxim.androidclient '
            }]
    },
    {
        'name': _('Bruno'),
        'description': _('Bruno is a themed version of the open source '
                         'yaxim app.'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'google_play_store',
                'fully_qualified_name': 'org.yaxim.bruno',
                'url': 'https://play.google.com/store/apps/details?id'
                       '=org.yaxim.bruno '
            }
        ]
    },
    {
        'name': _('Chat secure - Encrypted Messenger'),
        'description': _('ChatSecure is a free and open source '
                         'messaging app that features OTR encryption '
                         'over XMPP. You can connect to an existing '
                         'Google account, create new accounts on '
                         'public XMPP servers (including via Tor), '
                         'or even connect to your own server for '
                         'extra security.'),
        'platforms': [
            {
                'type': 'store',
                'os': 'iOS',
                'store_name': 'apple_store',
                'url': 'https://itunes.apple.com/us/app/chatsecure'
                       '/id464200063 '
            }
        ]
    },
    {
        'name': _('Conversations'),
        'platforms': [
            {
                'type': 'store',
                'os': 'Android',
                'store_name': 'google_play_store',
                'url': 'https://play.google.com/store/apps/details?id'
                       '=eu.siacs.conversations ',
                'fully_qualified_name': 'eu.siacs.conversations'
            }
        ]
    },
    {
        'name': _('Dino'),
        'platforms': [
            {
                'type': 'download',
                'os': 'Debian',
                'url': 'https://download.opensuse.org/repositories/network'
                       ':/messaging:/xmpp:/dino/Debian_9.0/amd64/dino_0.0'
                       '~git178.9d8e1e8_amd64.deb',
            }
        ]
    },
    {
        'name': _('Gajim'),
        'platforms': [
            {
                'type': 'apt',
                'os': 'Debian',
                'package_name': 'gajim'
            },
            {
                'type': 'download',
                'os': 'Windows',
                'url': 'https://gajim.org/downloads/0.16/gajim-0.16.8-2.exe'
            }
        ]
    },
    {
        'name': _('OneTeam'),
        'platforms': [
            {
                'type': 'download',
                'os': 'Windows',
                'url': 'https://download.process-one.net/oneteam/release'
                       '-installers/OneTeam.msi'
            },
            {
                'type': 'download',
                'os': 'macOS',
                'url': 'https://download.process-one.net/oneteam/release'
                       '-installers/OneTeam.dmg '
            },
            {
                'type': 'download',
                'os': 'Linux',
                'url': 'https://download.process-one.net/oneteam/release'
                       '-installers/oneteam.tar.bz2 '
            }
        ]
    }
].append(jsxc_manifest.clients)
