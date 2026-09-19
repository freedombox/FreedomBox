# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('WordPress'),
    'platforms': [{
        'type': 'web',
        'url': '/wordpress/'
    }]
}]

backup = {
    'data': {
        'files': [
            '/var/lib/plinth/backups-data/wordpress-database.sql',
            '/etc/wordpress/is_public'
        ],
        'directories': ['/var/lib/wordpress/']
    },
    'secrets': {
        'directories': ['/etc/wordpress/']
    },
}

tags = [_('Website'), _('Blog'), _('Content management system')]
