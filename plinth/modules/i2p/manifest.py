# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for I2P.
"""

from django.utils.translation import gettext_lazy as _

_package_id = 'net.geti2p.i2p'
_download_url = 'https://geti2p.net/download'

clients = [{
    'name':
        _('I2P'),
    'platforms': [{
        'type': 'web',
        'url': '/i2p/'
    }, {
        'type': 'package',
        'format': 'deb',
        'name': 'i2p',
    }, {
        'type': 'download',
        'os': 'gnu-linux',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'macos',
        'url': _download_url,
    }, {
        'type': 'download',
        'os': 'windows',
        'url': _download_url,
    }]
}]

backup = {
    'secrets': {
        'directories': ['/var/lib/i2p/i2p-config']
    },
    'services': ['i2p']
}

tags = [_('Anonymity network'), _('Censorship resistance')]
