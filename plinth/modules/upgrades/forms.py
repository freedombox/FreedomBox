# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring unattended-upgrades.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class ConfigureForm(forms.Form):
    """Configuration form to enable/disable automatic upgrades."""
    auto_upgrades_enabled = forms.BooleanField(
        label=_('Enable auto-update'), required=False, help_text=_(
            'When enabled, FreedomBox automatically updates once a day.'))

    dist_upgrade_enabled = forms.BooleanField(
        label=_('Enable auto-update to next stable release'), required=False,
        help_text=_('When enabled, FreedomBox will upgrade to the next stable '
                    'distribution release when it is available.'))


class BackportsFirstbootForm(forms.Form):
    """Form to configure backports during first boot wizard."""
    backports_enabled = forms.BooleanField(
        label=_('Activate frequent feature updates (recommended)'),
        required=False, initial=True)
