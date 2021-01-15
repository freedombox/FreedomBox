# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

clients = [{
    'name': _('Transmission'),
    'platforms': [{
        'type': 'web',
        'url': '/transmission'
    }]
}]

backup = {
    'data': {
        'directories': ['/var/lib/transmission-daemon/.config']
    },
    'secrets': {
        'files': ['/etc/transmission-daemon/settings.json']
    },
    'services': ['transmission-daemon']
}
