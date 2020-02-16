# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name': _('Transmission'),
    'platforms': [{
        'type': 'web',
        'url': '/transmission'
    }]
}])

backup = validate_backup({
    'data': {
        'directories': ['/var/lib/transmission-daemon/.config']
    },
    'secrets': {
        'files': ['/etc/transmission-daemon/settings.json']
    },
    'services': ['transmission-daemon']
})
