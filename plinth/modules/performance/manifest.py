# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for System Monitoring (cockpit-pcp) in ‘System’.
"""

from django.utils.translation import ugettext_lazy as _
from plinth.clients import validate

clients = validate([{
    'name': _('Cockpit'),
    'platforms': [{
        'type': 'web',
        'url': '/_cockpit/'
    }]
}])
