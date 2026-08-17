# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for Deluge app.
"""

from django.utils.translation import gettext_lazy as _

from plinth.modules.storage.forms import (DirectorySelectForm,
                                          DirectoryValidator)

from . import SYSTEM_USER


class DelugeForm(DirectorySelectForm):
    """Deluge configuration form"""

    def __init__(self, *args, **kw):
        validator = DirectoryValidator(username=SYSTEM_USER,
                                       check_creatable=True)
        super().__init__(title=_('Download directory'),
                         default='/var/lib/deluged/Downloads',
                         validator=validator, *args, **kw)
