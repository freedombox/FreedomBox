# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring Ejabberd.
"""

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth.utils import format_lazy


class EjabberdForm(forms.Form):
    """Ejabberd configuration form."""
    MAM_enabled = forms.BooleanField(
        label=_('Enable Message Archive Management'), required=False,
        help_text=format_lazy(
            _('If enabled, your {box_name} will store chat message histories. '
              'This allows synchronization of conversations between multiple '
              'clients, and reading the history of a multi-user chat room. '
              'It depends on the client settings whether the histories are '
              'stored as plain text or encrypted.'), box_name=_(cfg.box_name)))

    enable_managed_turn = forms.BooleanField(
        label=_('Automatically manage audio/video call setup'), required=False,
        help_text=format_lazy(
            _('Configures the local <a href={coturn_url}>coturn</a> app as '
              'the STUN/TURN server for ejabberd. Disable this if you '
              'want to use a different STUN/TURN server.'),
            coturn_url=reverse_lazy('coturn:index')))

    # STUN/TURN server setup
    turn_uris = forms.CharField(
        label=_('STUN/TURN Server URIs'), required=False, strip=True,
        widget=forms.Textarea(attrs={'rows': 4}),
        help_text=_('List of public URIs of the STUN/TURN server, one on each '
                    'line.'))

    shared_secret = forms.CharField(
        label=_('Shared Authentication Secret'), required=False, strip=True,
        help_text=_('Shared secret used to compute passwords for the '
                    'TURN server.'))

    def clean_turn_uris(self):
        """Normalize newlines in URIs."""
        data = self.cleaned_data['turn_uris']
        return '\n'.join([uri.strip() for uri in data.splitlines()])
