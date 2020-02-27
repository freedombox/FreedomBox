# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.modules.backups.api import validate as validate_backup
from plinth.clients import validate

clients = validate([{
    'name': _('ikiwiki'),
    'platforms': [{
        'type': 'web',
        'url': '/ikiwiki'
    }]
}])

backup = validate_backup(
    {'data': {
        'directories': ['/var/lib/ikiwiki/', '/var/www/ikiwiki/']
    }})
