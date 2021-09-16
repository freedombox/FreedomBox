# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Roundcube'),
    'platforms': [{
        'type': 'web',
        'url': '/roundcube'
    }]
}]

backup = {}
