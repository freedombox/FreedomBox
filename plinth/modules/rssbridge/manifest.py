# SPDX-License-Identifier: AGPL-3.0-or-later

from django.utils.translation import gettext_lazy as _

"""
Application manifest for RSS-Bridge.
"""

clients = [{
    'name': _('RSS-Bridge'),
    'platforms': [{
        'type': 'web',
        'url': '/rss-bridge/'
    }]
}]

backup = {}
