# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for System Monitoring (cockpit-pcp) in ‘System’.
"""

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Cockpit'),
    'platforms': [{
        'type': 'web',
        'url': '/_cockpit/metrics'
    }]
}]

backup: dict = {}

tags = [_('Monitoring'), _('Resource utilization')]
