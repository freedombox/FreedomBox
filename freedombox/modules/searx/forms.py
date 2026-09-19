# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django form for configuring Searx."""

from django import forms
from django.utils.translation import gettext_lazy as _


class SearxForm(forms.Form):
    """Searx configuration form."""

    safe_search = forms.ChoiceField(
        label=_('Safe Search'), help_text=_(
            'Select the default family filter to apply to your search results.'
        ), choices=((0, _('None')), (1, _('Moderate')), (2, _('Strict'))))

    public_access = forms.BooleanField(
        label=_('Allow Public Access'), help_text=_(
            'Allow this application to be used by anyone who can reach it.'),
        required=False)
