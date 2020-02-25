# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring Transmission.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.modules.transmission import reserved_usernames
from plinth.modules.storage.forms import (DirectorySelectForm,
                                          DirectoryValidator)


class TransmissionForm(DirectorySelectForm):
    """Transmission configuration form"""

    def __init__(self, *args, **kw):
        validator = DirectoryValidator(
            username=reserved_usernames[0], check_writable=True)
        super(TransmissionForm, self).__init__(
            title=_('Download directory'),
            default='/var/lib/transmission-daemon/downloads',
            validator=validator, *args, **kw)
