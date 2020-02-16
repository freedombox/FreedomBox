# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for cockpit.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.modules.backups.api import validate as validate_backup
from plinth.clients import validate

clients = validate([{
    'name': _('Cockpit'),
    'platforms': [{
        'type': 'web',
        'url': '/_cockpit/'
    }]
}])

# cockpit.conf need not be backed up because add/remove domain signals are
# triggered on every Plinth domain change (and cockpit application install) and
# will set the value of allowed domains correctly. This is the only key the is
# customized in cockpit.conf.
backup = validate_backup({})
