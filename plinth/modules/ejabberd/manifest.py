# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import store_url
from plinth.modules.jsxc import manifest as jsxc_manifest

_clients = [{
    'name':
        _('Conversations'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'eu.siacs.conversations')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'eu.siacs.conversations')
    }]
}, {
    'name':
        _('Xabber'),
    'description':
        _('Open source Jabber (XMPP) client with multi-account support '
          'and clean and simple interface. '),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'com.xabber.androiddev')
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'com.xabber.android')
    }]
}, {
    'name':
        _('Yaxim'),
    'platforms': [{
        'type': 'store',
        'os': 'android',
        'store_name': 'f-droid',
        'url': store_url('f-droid', 'org.yaxim.androidclient'),
    }, {
        'type': 'store',
        'os': 'android',
        'store_name': 'google-play',
        'url': store_url('google-play', 'org.yaxim.androidclient'),
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
        'url': 'https://apps.apple.com/us/app/chatsecure/id464200063'
    }]
}, {
    'name':
        _('Dino'),
    'platforms': [{
        'type': 'download',
        'os': 'gnu-linux',
        'url': 'https://github.com/dino/dino/wiki/Distribution-Packages',
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'dino-im'
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
        'os': 'gnu-linux',
        'url': 'https://gajim.org/downloads.php'
    }, {
        'type': 'download',
        'os': 'macos',
        'url': 'https://gajim.org/downloads.php'
    }, {
        'type': 'download',
        'os': 'windows',
        'url': 'https://gajim.org/downloads.php'
    }]
}]

_clients.extend(jsxc_manifest.clients)

clients = _clients

backup = {
    'config': {
        'files': ['/etc/ejabberd/ejabberd.yml']
    },
    'data': {
        'directories': ['/var/lib/ejabberd/']
    },
    'secrets': {
        'files': ['/etc/ejabberd/ejabberd.pem'],
        'directories': ['/etc/ejabberd/letsencrypt/']
    },
    'services': ['ejabberd']
}
