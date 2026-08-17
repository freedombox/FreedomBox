# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Shadowsocks Server.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'secrets': {
        'files': [
            '/var/lib/private/shadowsocks-libev/fbxserver/fbxserver.json'
        ]
    },
    'services': ['shadowsocks-libev-server@fbxserver']
}

tags = [
    _('Censorship resistance'),
    _('Encrypted tunnel'),
    _('Exit point'),
    _('Shadowsocks')
]
