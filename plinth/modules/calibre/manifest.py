# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('calibre'),
    'platforms': [{
        'type': 'web',
        'url': '/calibre/'
    }]
}]

backup = {
    'data': {
        'directories': ['/var/lib/private/calibre-server-freedombox/']
    },
    'services': ['calibre-server-freedombox']
}

tags = [_('Ebook'), _('Library'), _('Ebook reader')]
