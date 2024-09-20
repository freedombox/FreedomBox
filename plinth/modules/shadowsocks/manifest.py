# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Shadowsocks Client.
"""

from django.utils.translation import gettext_lazy as _

backup = {
    'secrets': {
        'files': [
            '/var/lib/private/shadowsocks-libev/freedombox/freedombox.json'
        ]
    },
    'services': ['shadowsocks-libev-local@freedombox']
}

tags = [
    _('Proxy'),
    _('Client'),
    _('SOCKS5'),
    _('Censorship Resistance'),
    _('Shadowsocks')
]
