# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Searx'),
    'platforms': [{
        'type': 'web',
        'url': '/searx/'
    }]
}]

PUBLIC_ACCESS_SETTING_FILE = '/etc/searx/allow_public_access'

backup = {'config': {'files': [PUBLIC_ACCESS_SETTING_FILE]}}

tags = [_('Web search'), _('Metasearch Engine')]
