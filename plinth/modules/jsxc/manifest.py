# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

clients = validate([{
    'name': _('JSXC'),
    'platforms': [{
        'type': 'web',
        'url': reverse_lazy('jsxc:jsxc')
    }]
}])

backup = validate_backup({})
