# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the Kiwix module.
"""

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _

from plinth import cfg

from .privileged import KIWIX_HOME


class AddContentForm(forms.Form):
    """Form to create an empty library."""

    # Would be nice to have a progress bar when uploading large files.
    file = forms.FileField(
        label=_('Upload File'), required=True, validators=[
            validators.FileExtensionValidator(
                ['zim'], _('Content packages have to be in .zim format'))
        ], help_text=_(f'''Uploaded ZIM files will be stored under
        {KIWIX_HOME}/content on your {cfg.box_name}. If Kiwix fails to add the file,
        it will be deleted immediately to save disk space.'''))
