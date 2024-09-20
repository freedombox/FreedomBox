# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('bepasty'),
    'platforms': [{
        'type': 'web',
        'url': '/bepasty'
    }]
}]

backup = {
    'config': {
        'files': ['/etc/bepasty-freedombox.conf']
    },
    'data': {
        'directories': ['/var/lib/bepasty']
    },
    'services': ['uwsgi'],
}

tags = [_('File Sharing'), _('Pastebin')]
