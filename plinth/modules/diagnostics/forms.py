# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for configuring diagnostics."""

from django import forms
from django.utils.translation import gettext_lazy as _


class ConfigureForm(forms.Form):
    """Configuration form to enable/disable daily diagnostics run."""
    daily_run_enabled = forms.BooleanField(
        label=_('Enable daily run'), required=False,
        help_text=_('When enabled, diagnostic checks will run once a day.'))

    automatic_repair = forms.BooleanField(
        label=_('Enable automatic repair'), required=False,
        help_text=_('If issues are found, try to repair them automatically.'))
