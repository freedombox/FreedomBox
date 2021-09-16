# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring Transmission.
"""

from django.utils.translation import gettext_lazy as _

from plinth.modules.storage.forms import (DirectorySelectForm,
                                          DirectoryValidator)

from . import SYSTEM_USER


class TransmissionForm(DirectorySelectForm):
    """Transmission configuration form"""

    def __init__(self, *args, **kw):
        validator = DirectoryValidator(username=SYSTEM_USER,
                                       check_creatable=True)
        super(TransmissionForm,
              self).__init__(title=_('Download directory'),
                             default='/var/lib/transmission-daemon/downloads',
                             validator=validator, *args, **kw)
