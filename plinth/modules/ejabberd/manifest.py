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
from plinth.templatetags.plinth_extras import Desktop_OS, Mobile_OS, Store
from plinth.utils import play_store_url

yaxim_package_id = 'org.yaxim.androidclient'
bruno_package_id = 'org.yaxim.bruno'
conversations_package_id = 'eu.siacs.conversations'

_clients = [{
    'name':
        _('yaxim'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': play_store_url(yaxim_package_id),
    }]
}, {
    'name':
        _('Bruno'),
    'description':
        _('Bruno is a themed version of the open source '
          'yaxim app.'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': play_store_url(bruno_package_id)
    }]
}, {
    'name':
        _('Chat secure - Encrypted Messenger'),
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
        'os': Mobile_OS.IOS.value,
        'store_name': Store.APP_STORE.value,
        'url': 'https://itunes.apple.com/us/app/chatsecure'
               '/id464200063 '
    }]
}, {
    'name':
        _('Conversations'),
    'platforms': [{
        'type': 'store',
        'os': Mobile_OS.ANDROID.value,
        'store_name': Store.GOOGLE_PLAY.value,
        'url': play_store_url(conversations_package_id)
    }]
}, {
    'name':
        _('Dino'),
    'platforms': [{
        'type': 'download',
        'os': Desktop_OS.GNU_LINUX,
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
        'os': Desktop_OS.WINDOWS.value,
        'url': 'https://gajim.org/downloads.php'
    }]
}]

_clients.extend(jsxc_manifest.clients)

clients = _clients
