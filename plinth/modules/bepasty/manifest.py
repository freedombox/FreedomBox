# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name': _('bepasty'),
    'platforms': [{
        'type': 'web',
        'url': '/bepasty'
    }]
}])

backup = validate_backup({
    'config': {
        'files': ['/etc/bepasty-freedombox.conf']
    },
    'data': {
        'directories': ['/var/lib/bepasty']
    },
    'services': ['uwsgi'],
})
