# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox configuration form for MiniDLNA server.
"""

from django.utils.translation import gettext_lazy as _

from plinth.modules.storage.forms import (DirectorySelectForm,
                                          DirectoryValidator)

from . import SYSTEM_USER


class MiniDLNAServerForm(DirectorySelectForm):
    """MiniDLNA server configuration form."""

    def __init__(self, *args, **kw):
        validator = DirectoryValidator(username=SYSTEM_USER)
        super().__init__(
            title=_('Media Files Directory'), help_text=_(
                'Directory that MiniDLNA Server will read for content. All '
                'sub-directories of this will be also scanned for media files.'
            ), default='/var/lib/minidlna', validator=validator, *args, **kw)
