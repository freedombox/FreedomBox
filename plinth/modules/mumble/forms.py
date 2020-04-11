# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Mumble server configuration form
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class MumbleForm(forms.Form):
    """Mumble server configuration"""
    super_user_password = forms.CharField(
        max_length=20,
        label=_('Set SuperUser Password'),
        widget=forms.PasswordInput,
        help_text=_(
            'Optional. Leave this field blank to keep the current password. '
            'SuperUser password can be used to manage permissions in Mumble.'),
        required=False,
    )
