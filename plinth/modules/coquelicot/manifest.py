# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backups

clients = validate([{
    'name': _('coquelicot'),
    'platforms': [{
        'type': 'web',
        'url': '/coquelicot'
    }]
}])

backup = validate_backups({
    'data': {
        'directories': ['/var/lib/coquelicot']
    },
    'secrets': {
        'files': ['/etc/coquelicot/settings.yml']
    },
    'services': ['coquelicot']
})
