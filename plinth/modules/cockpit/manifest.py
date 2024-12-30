# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for cockpit.
"""

from django.utils.translation import gettext_lazy as _

clients = [{
    'name': _('Cockpit'),
    'platforms': [{
        'type': 'web',
        'url': '/_cockpit/'
    }]
}]

# cockpit.conf need not be backed up because add/remove domain signals are
# triggered on every Plinth domain change (and cockpit application install) and
# will set the value of allowed domains correctly. This is the only key the is
# customized in cockpit.conf.
backup: dict = {}

tags = [
    _('Advanced administration'),
    _('Web terminal'),
    _('Storage'),
    _('Networking'),
    _('Services'),
    _('Logs'),
    _('Performance'),
]
