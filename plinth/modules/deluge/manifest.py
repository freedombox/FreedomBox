# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Deluge'),
    'description': _('Bittorrent client written in Python/PyGTK'),
    'platforms': [{
        'type': 'web',
        'url': '/deluge'
    }]
}]

backup = {
    'config': {
        'directories': ['/var/lib/deluged/.config']
    },
    'services': ['deluged', 'deluge-web']
}

tags = [_('File Sharing'), _('BitTorrent'), _('Client'), _('P2P')]
