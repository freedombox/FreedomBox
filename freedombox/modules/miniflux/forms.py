# SPDX-License-Identifier: AGPL-3.0-or-later

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class UserCredentialsForm(forms.Form):
    """Form to create admin user or change a user's password."""

    username = forms.CharField(label=_('Username'),
                               help_text=_('Enter a username for the user.'))
    password = forms.CharField(
        label=_('Password'), widget=forms.PasswordInput, min_length=6,
        strip=False,
        help_text=_('Enter a strong password with a minimum of 6 characters.'))
    password_confirmation = forms.CharField(
        label=_('Password confirmation'), widget=forms.PasswordInput,
        min_length=6, strip=False,
        help_text=_('Enter the same password for confirmation.'))

    def clean(self):
        """Raise error if passwords don't match."""
        cleaned_data = super().clean()
        password = self.cleaned_data.get('password')
        password_confirmation = self.cleaned_data.get('password_confirmation')

        if password and password_confirmation and (password
                                                   != password_confirmation):
            self.add_error('password_confirmation',
                           ValidationError(_('Passwords do not match.')))

        return cleaned_data
