# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for Deluge app.
"""

from django.utils.translation import ugettext_lazy as _

from plinth.modules.deluge import reserved_usernames
from plinth.modules.storage.forms import (DirectorySelectForm,
                                          DirectoryValidator)


class DelugeForm(DirectorySelectForm):
    """Deluge configuration form"""

    def __init__(self, *args, **kw):
        validator = DirectoryValidator(username=reserved_usernames[0],
                                       check_creatable=True)
        super(DelugeForm, self).__init__(
            title=_('Download directory'),
            default='/var/lib/deluged/Downloads/', validator=validator, *args,
            **kw)
