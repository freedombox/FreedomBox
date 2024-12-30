# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Application manifest for backups.
"""

from django.utils.translation import gettext_lazy as _

# Currently, backup application does not have any settings. However, settings
# such as scheduler settings, backup location, secrets to connect to remove
# servers need to be backed up.
backup: dict = {}

tags = [
    _('Restore'),
    _('Encrypted'),
    _('Schedules'),
    _('Local'),
    _('Remote'),
    _('App data'),
    _('Configuration'),
    _('Borg')
]
