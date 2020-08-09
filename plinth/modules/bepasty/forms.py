# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django forms for bepasty app.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.modules import bepasty


class SetDefaultPermissionsForm(forms.Form):
    """Form to set default permissions"""
    default_permissions = forms.ChoiceField(
        choices=bepasty.DEFAULT_PERMISSIONS.items(), required=False,
        widget=forms.RadioSelect(),
        label=_('Public Access (default permissions)'),
        help_text=_('Permissions for anonymous users, who have not provided a '
                    'password.'))


class AddPasswordForm(forms.Form):
    """Form to add a new password."""

    permissions = forms.MultipleChoiceField(
        choices=bepasty.PERMISSIONS.items(),
        widget=forms.CheckboxSelectMultiple, required=False,
        label=_('Permissions'), help_text=_(
            'Users that log in with this password will have the selected '
            'permissions.'))

    comment = forms.CharField(
        label=_('Comment'), required=False, strip=True, help_text=_(
            'Any comment to help you remember the purpose of this password.'))
