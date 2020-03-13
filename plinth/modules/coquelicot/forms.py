# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Plinth form for configuring Coquelicot.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class CoquelicotForm(forms.Form):  # pylint: disable=W0232
    """Coquelicot configuration form."""
    upload_password = forms.CharField(
        label=_('Upload Password'),
        help_text=_('Set a new upload password for Coquelicot. '
                    'Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput)
    max_file_size = forms.IntegerField(
        label=_("Maximum File Size (in MiB)"), help_text=_(
            'Set the maximum size of the files that can be uploaded to '
            'Coquelicot.'), required=False, min_value=0)
