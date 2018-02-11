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

from plinth.modules.jsxc import manifest as jsxc_manifest
from plinth.clients import store_url, validate

_clients = validate([{
    'name':
        _('yaxim'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'org.yaxim.androidclient'),
    }]
}, {
    'name':
        _('Bruno'),
    'description':
        _('Bruno is a themed version of the open source '
          'yaxim app.'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'org.yaxim.bruno')
    }]
}, {
    'name':
        _('ChatSecure'),
    'description':
        _('ChatSecure is a free and open source '
          'messaging app that features OTR encryption '
          'over XMPP. You can connect to an existing '
          'Google account, create new accounts on '
          'public XMPP servers (including via Tor), '
          'or even connect to your own server for '
          'extra security.'),
    'platforms': [{
        'type': 'store',
        'os': 'ios',
        'store_name': 'app-store',
        'url': 'https://itunes.apple.com/us/app/chatsecure'
               '/id464200063'
    }]
}, {
    'name':
        _('Conversations'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'eu.siacs.conversations')
    }]
}, {
    'name':
        _('Dino'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://github.com/dino/dino/wiki/Distribution-Packages',
    }]
}, {
    'name':
        _('Gajim'),
    'platforms': [{
        'type': 'package',
        'format': 'deb',
        'name': 'gajim'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://gajim.org/downloads.php'
    }]
}])

_clients.extend(jsxc_manifest.clients)

clients = _clients
