# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django forms for configuring TiddlyWiki."""

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _


def _validate_not_index_file(name):
    """Validate that the normalized file name is not 'index.html'."""
    if str(name) in ('index.html', 'index'):
        raise forms.ValidationError(
            _('Wiki files cannot be named "index.html".'))


class CreateWikiForm(forms.Form):
    """Form to create a new wiki file."""

    name = forms.CharField(
        label=_('Name of the wiki file, with file extension ".html"'),
        strip=True, validators=[_validate_not_index_file], help_text=_(
            'Wiki title and description can be set from within the wiki. '
            'This file name is independent of the wiki title.'))


class RenameWikiForm(forms.Form):
    """Form to rename a wiki file."""

    new_name = forms.CharField(
        label=_('New name for the wiki file, with file extension ".html"'),
        strip=True, validators=[_validate_not_index_file], help_text=_(
            'Renaming the file has no effect on the title of the wiki.'))


class UploadWikiForm(forms.Form):
    """Form to upload a wiki file."""

    file = forms.FileField(
        label=_('A TiddlyWiki file with .html file extension'), required=True,
        validators=[
            validators.FileExtensionValidator(
                ['html'],
                _('TiddlyWiki files must be in HTML format'),
            ), _validate_not_index_file
        ],
        help_text=_('Upload an existing TiddlyWiki file from this computer.'))
