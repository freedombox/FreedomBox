# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django form for configuring calibre."""

from django import forms
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from . import privileged


class CreateLibraryForm(forms.Form):
    """Form to create an empty library."""

    name = forms.CharField(
        label=_('Name of the new library'), strip=True,
        help_text=_('Only letters of the English alphabet, numbers '
                    'and the characters _ . and - without spaces or '
                    'special characters. Example: My_Library_2000'),
        validators=[validators.RegexValidator(r'^[A-Za-z0-9_.-]+$')])

    def clean_name(self):
        """Check if the library name is valid."""
        name = self.cleaned_data['name']

        if name in privileged.list_libraries():
            raise ValidationError(
                _('A library with this name already exists.'))

        return name
