# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring unattended-upgrades.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.modules import upgrades


class ConfigureForm(forms.Form):
    """Configuration form to enable/disable automatic upgrades."""
    auto_upgrades_enabled = forms.BooleanField(
        label=_('Enable auto-update'), required=False, help_text=_(
            'When enabled, FreedomBox automatically updates once a day.'))

    dist_upgrade_enabled = forms.BooleanField(
        label=_('Enable auto-update to next stable release'), required=False,
        help_text=_('When enabled, FreedomBox will update to the next stable '
                    'distribution release when it is available.'))

    def __init__(self, *args, **kwargs):
        """Disable options as necessary."""
        super().__init__(*args, **kwargs)

        self.fields['dist_upgrade_enabled'].disabled = \
            not upgrades.can_enable_dist_upgrade()


class BackportsFirstbootForm(forms.Form):
    """Form to configure backports during first boot wizard."""
    backports_enabled = forms.BooleanField(
        label=_('Activate frequent feature updates (recommended)'),
        required=False, initial=True)
