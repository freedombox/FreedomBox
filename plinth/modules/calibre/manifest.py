# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name': _('calibre'),
    'platforms': [{
        'type': 'web',
        'url': '/calibre/'
    }]
}])

backup = validate_backup({
    'data': {
        'directories': ['/var/lib/private/calibre-server-freedombox/']
    },
    'services': ['calibre-server-freedombox']
})
