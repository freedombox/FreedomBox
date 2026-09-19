# SPDX-License-Identifier: AGPL-3.0-or-later
"""Nextcloud configuration form."""

from django import forms
from django.utils.translation import gettext_lazy as _


def _get_phone_regions():
    """Return choice field choices for phone regions."""
    try:
        from iso3166 import countries  # type: ignore
        phone_regions = [(country.alpha2, country.name)
                         for country in countries]
        phone_regions = sorted(phone_regions)
    except ImportError:
        # Allow users to set a non-empty value
        phone_regions = [('US', 'United States of America')]

    return [('', _('Not set'))] + phone_regions


class NextcloudForm(forms.Form):
    """Nextcloud configuration form."""

    override_domain = forms.CharField(
        label=_('Override domain'), required=False, help_text=_(
            'Set to the domain or IP address that Nextcloud should be forced '
            'to generate URLs with. Should not be needed if a valid domain is '
            'used to access Nextcloud. Examples: "myfreedombox.example.org" '
            'or "example.onion".'))

    admin_password = forms.CharField(
        label=_('Administrator password'), help_text=_(
            'Optional. Set a new password for Nextcloud\'s administrator '
            'account (nextcloud-admin). The password cannot be a common one '
            'and the minimum required length is <strong>10 characters'
            '</strong>. Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput, min_length=10)

    default_phone_region = forms.ChoiceField(
        label=_('Default phone region'), required=False,
        help_text=_('The default phone region is required to validate phone '
                    'numbers in the profile settings without a country code.'),
        choices=_get_phone_regions)
