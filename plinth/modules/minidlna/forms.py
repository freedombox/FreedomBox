# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox configuration form for MiniDLNA server.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm


class MiniDLNAServerForm(AppForm):
    """MiniDLNA server configuration form."""
    media_dir = forms.CharField(
        label=_('Media Files Directory'),
        help_text=_('Directory that MiniDLNA Server will read for content. All'
                    ' sub-directories of this will be also scanned for media '
                    'files. '
                    'If you change the default ensure that the new directory '
                    'exists and that is readable from the "minidlna" user. '
                    'Any user media directories ("/home/username/") will '
                    'usually work.'),
        required=False,
    )
