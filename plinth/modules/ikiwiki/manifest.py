# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate

clients = validate([{
    'name': _('ikiwiki'),
    'platforms': [{
        'type': 'web',
        'url': '/ikiwiki'
    }]
}])

backup = {'data': {'directories': ['/var/lib/ikiwiki/', '/var/www/ikiwiki/']}}
