# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django forms for configuring Feather Wiki."""

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _


class CreateWikiForm(forms.Form):
    """Form to create a new wiki file."""

    name = forms.CharField(
        label=_('Name of the wiki file, with file extension ".html"'),
        strip=True, help_text=_(
            'Wiki title and description can be set from within the wiki. '
            'This file name is independent of the wiki title.'))


class RenameWikiForm(forms.Form):
    """Form to rename a wiki file."""

    new_name = forms.CharField(
        label=_('New name for the wiki file, with file extension ".html"'),
        strip=True, help_text=_(
            'Renaming the file has no effect on the title of the wiki.'))


class UploadWikiForm(forms.Form):
    """Form to upload a wiki file."""

    file = forms.FileField(
        label=_('A Feather Wiki file with .html file extension'),
        required=True, validators=[
            validators.FileExtensionValidator(
                ['html'], _('Feather Wiki files must be in HTML format'))
        ], help_text=_(
            'Upload an existing Feather Wiki file from this computer.'))
