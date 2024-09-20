# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

from plinth.clients import validate

clients = validate([{
    'name': _('Kiwix'),
    'platforms': [{
        'type': 'web',
        'url': '/kiwix'
    }]
}])

backup = {
    'data': {
        'directories': ['/var/lib/private/kiwix-server-freedombox/']
    },
    'services': ['kiwix-server-freedombox']
}

tags = [_('Offline Reader'), _('Archival'), _('Censorship Resistance')]
