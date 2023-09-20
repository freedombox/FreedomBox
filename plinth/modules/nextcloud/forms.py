# SPDX-License-Identifier: AGPL-3.0-or-later
"""Nextcloud configuration form."""

from django import forms
from django.utils.translation import gettext_lazy as _


class NextcloudForm(forms.Form):
    """Nextcloud configuration form."""

    domain = forms.CharField(
        label=_('Domain'), required=False, help_text=_(
            'Examples: "myfreedombox.example.org" or "example.onion".'))

    admin_password = forms.CharField(
        label=_('Administrator password'), help_text=_(
            'Optional. Set a new password for Nextcloud\'s administrator '
            'account (nextcloud-admin). The password cannot be a common one '
            'and the minimum required length is <strong>10 characters'
            '</strong>. Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput, min_length=10)
