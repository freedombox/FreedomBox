# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('ikiwiki'),
    'platforms': [{
        'type': 'web',
        'url': '/ikiwiki'
    }]
}]

backup = {'data': {'directories': ['/var/lib/ikiwiki/', '/var/www/ikiwiki/']}}

tags = [_('Wiki'), _('Blog'), _('Website')]
