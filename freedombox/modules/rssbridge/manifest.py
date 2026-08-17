# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for RSS-Bridge."""

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('RSS-Bridge'),
    'platforms': [{
        'type': 'web',
        'url': '/rss-bridge/'
    }]
}]

backup = {'data': {'files': ['/etc/rss-bridge/is_public']}}

tags = [_('Feed generator'), _('News'), _('RSS'), _('ATOM')]
