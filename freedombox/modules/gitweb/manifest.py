# SPDX-License-Identifier: AGPL-3.0-or-later

import pathlib

from django.utils.translation import gettext_lazy as _

GIT_REPO_PATH = pathlib.Path('/var/lib/git')
REPO_DIR_OWNER = 'www-data'

clients = [
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
]

backup = {'data': {'directories': [str(GIT_REPO_PATH)]}}

tags = [_('Git hosting'), _('Version control'), _('Developer tool')]
