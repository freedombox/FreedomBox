# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Roundcube'),
    'platforms': [{
        'type': 'web',
        'url': '/roundcube'
    }]
}]

backup = {
    'data': {
        'files': [
            '/etc/roundcube/freedombox-config.php',
            '/var/lib/dbconfig-common/sqlite3/roundcube/roundcube'
        ]
    }
}

tags = [_('Email'), _('Contacts'), _('Client')]
