# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import ugettext_lazy as _

from plinth.clients import validate
from plinth.modules.backups.api import validate as validate_backup

CONFIG_FILE = '/etc/gitweb-freedombox.conf'
GIT_REPO_PATH = '/var/lib/git'

clients = validate([
    {
        'name': _('Gitweb'),
        'platforms': [{
            'type': 'web',
            'url': '/gitweb/'
        }]
    },
    {
        'name':
            _('Git'),
        'platforms': [{
            'type': 'download',
            'os': 'gnu-linux',
            'url': 'https://git-scm.com/download/linux'
        }, {
            'type': 'download',
            'os': 'macos',
            'url': 'https://git-scm.com/download/mac'
        }, {
            'type': 'download',
            'os': 'windows',
            'url': 'https://git-scm.com/download/windows'
        }]
    },
])

backup = validate_backup({
    'config': {
        'files': [CONFIG_FILE]
    },
    'data': {
        'directories': [GIT_REPO_PATH]
    }
})
