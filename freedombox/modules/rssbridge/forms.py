# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django forms for configuring RSS-Bridge."""

from django import forms
from django.utils.translation import gettext_lazy as _


class RSSBridgeForm(forms.Form):
    """RSS-Bridge configuration form."""

    is_public = forms.BooleanField(
        label=_('Allow Public Access'), help_text=_(
            'Allow this application to be used by anyone who can reach it.'),
        required=False)
