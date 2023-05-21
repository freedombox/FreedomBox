# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for Shadowsocks Server.
"""

backup = {
    'secrets': {
        'files': [
            '/var/lib/private/shadowsocks-libev/fbxserver/fbxserver.json'
        ]
    },
    'services': ['shadowsocks-libev-server@fbxserver']
}
