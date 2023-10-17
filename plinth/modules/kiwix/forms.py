# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the Kiwix module.
"""

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy

from .privileged import KIWIX_HOME


class AddPackageForm(forms.Form):
    """Form to upload a content package to a library."""

    # Would be nice to have a progress bar when uploading large files.
    file = forms.FileField(
        label=_('Upload File'), required=True, validators=[
            validators.FileExtensionValidator(
                ['zim'], _('Content packages have to be in .zim format'))
        ], help_text=format_lazy(
            _('Uploaded ZIM files will be stored under {kiwix_home}/content '
              'on your {box_name}. If Kiwix fails to add the file, it will be '
              'deleted immediately to save disk space.'),
            box_name=_(cfg.box_name), kiwix_home=KIWIX_HOME))
