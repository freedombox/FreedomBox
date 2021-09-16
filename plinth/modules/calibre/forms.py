# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django form for configuring calibre.
"""

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from plinth.modules import calibre


class CreateLibraryForm(forms.Form):
    """Form to create an empty library."""

    name = forms.CharField(
        label=_('Name of the new library'), strip=True,
        validators=[validators.RegexValidator(r'^[A-Za-z0-9_.-]+$')])

    def clean_name(self):
        """Check if the library name is valid."""
        name = self.cleaned_data['name']

        if name in calibre.list_libraries():
            raise ValidationError(
                _('A library with this name already exists.'))

        return name
