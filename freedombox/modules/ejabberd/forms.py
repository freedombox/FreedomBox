# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring Ejabberd.
"""

from django import forms
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.modules import ejabberd
from plinth.modules.coturn.forms import turn_uris_validator
from plinth.modules.names.components import DomainName
from plinth.utils import format_lazy


class EjabberdForm(forms.Form):
    """Ejabberd configuration form."""
    domain_names = forms.MultipleChoiceField(
        label=_('Domain names'), widget=forms.CheckboxSelectMultiple,
        help_text=_(
            'Domains to be used by ejabberd. Note that user accounts are '
            'unique for each domain, and migrating users to a new domain name '
            'is not yet implemented.'), choices=[])

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
                    'line.'), validators=[turn_uris_validator])

    shared_secret = forms.CharField(
        label=_('Shared Authentication Secret'), required=False, strip=True,
        help_text=_('Shared secret used to compute passwords for the '
                    'TURN server.'))

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        # Start with any existing domains from ejabberd configuration.
        domains = ejabberd.get_domains()

        # Add other domains that can be configured.
        for domain in DomainName.list_names():
            if domain not in domains:
                domains.append(domain)

        self.fields['domain_names'].choices = zip(domains, domains)

    def clean_turn_uris(self):
        """Normalize newlines in URIs."""
        data = self.cleaned_data['turn_uris']
        return '\n'.join([uri.strip() for uri in data.splitlines()])
