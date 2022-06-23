# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Mumble server configuration form
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.modules import mumble


def get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    return ((domain, domain) for domain in mumble.get_available_domains())


class MumbleForm(forms.Form):
    """Mumble server configuration"""
    domain = forms.ChoiceField(
        choices=get_domain_choices,
        label=_('TLS domain'),
        help_text=_(
            'Select a domain to use TLS with. If the list is empty, please '
            'configure at least one domain with certificates.'),
        required=False,
    )

    super_user_password = forms.CharField(
        max_length=20,
        label=_('Set SuperUser Password'),
        widget=forms.PasswordInput,
        help_text=_(
            'Optional. Leave this field blank to keep the current password. '
            'SuperUser password can be used to manage permissions in Mumble.'),
        required=False,
    )

    join_password = forms.CharField(
        max_length=32,
        label=_('Set a password to join the server'),
        widget=forms.PasswordInput,
        help_text=_('Set a password that is required to join the server. '
                    'Leave empty to use the current password.'),
        required=False,
    )

    root_channel_name = forms.CharField(
        label=_('Set the name for the root channel'),
        min_length=1,
        max_length=32,
        help_text=_(
            'Set the name of the main channel of your mumble server. '
            'If the name was never changed, the channel is named Root.'),
        required=False,
    )
