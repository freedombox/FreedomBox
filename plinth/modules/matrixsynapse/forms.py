# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the Matrix Synapse module.
"""

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth.modules.coturn.forms import turn_uris_validator
from plinth.utils import format_lazy

_registration_verification_choices = [
    ('disabled',
     _('Disabled. This could lead to adversaries registering many spam '
       'accounts on your server with automated scripts.')),
    ('token',
     _('Require users creating a new account to use a registration token. A '
       'token will be created automatically. Pass this token to your '
       'potential new users. They will be asked for the token during '
       'registration. (recommended)')),
]


class MatrixSynapseForm(forms.Form):
    enable_public_registration = forms.BooleanField(
        label=_('Enable Public Registration'), required=False, help_text=_(
            'Enabling public registration means that anyone on the Internet '
            'can register a new account on your Matrix server. Disable this '
            'if you only want existing users to be able to use it.'))

    registration_verification = forms.ChoiceField(
        label=_('Verification method for registration'),
        choices=_registration_verification_choices, required=True,
        widget=forms.RadioSelect)

    enable_managed_turn = forms.BooleanField(
        label=_('Automatically manage audio/video call setup'), required=False,
        help_text=format_lazy(
            _('Configures the local <a href={coturn_url}>coturn</a> app as '
              'the STUN/TURN server for Matrix Synapse. Disable this if you '
              'want to use a different STUN/TURN server.'),
            coturn_url=reverse_lazy('coturn:index')))

    # STUN/TURN server setup
    turn_uris = forms.CharField(
        label=_('STUN/TURN Server URIs'), required=False, strip=True,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text=_('List of public URIs of the STUN/TURN server, one on each '
                    'line.'), validators=[turn_uris_validator])

    shared_secret = forms.CharField(
        label=_('Shared Authentication Secret'), required=False, strip=True,
        help_text=_('Shared secret used to compute passwords for the '
                    'TURN server.'))

    def clean_turn_uris(self):
        """Normalize newlines in URIs."""
        data = self.cleaned_data['turn_uris']
        return '\n'.join([uri.strip() for uri in data.splitlines()])
