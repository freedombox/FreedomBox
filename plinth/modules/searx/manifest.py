# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name': _('Searx'),
    'platforms': [{
        'type': 'web',
        'url': '/searx/'
    }]
}])

PUBLIC_ACCESS_SETTING_FILE = '/etc/searx/allow_public_access'

backup = validate_backup({'config': {'files': [PUBLIC_ACCESS_SETTING_FILE]}})
