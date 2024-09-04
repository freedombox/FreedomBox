# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for the names app."""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.utils import format_lazy


class NamesConfigurationForm(forms.Form):
    """Form to configure names app."""

    dns_over_tls = forms.ChoiceField(
        label=_('Use DNS-over-TLS for resolving domains (global preference)'),
        widget=forms.RadioSelect, choices=[
            ('yes',
             format_lazy(
                 'Yes. Encrypt connections to the DNS server. <p '
                 'class="help-block">This improves privacy as domain name '
                 'queries will not be made as plain text over the network. It '
                 'also improves security as responses from the server cannot '
                 'be manipulated. If the configured DNS servers do not '
                 'support DNS-over-TLS, all name resolutions will fail. If '
                 'your DNS provider (likely your ISP) does not support '
                 'DNS-over-TLS or blocks some domains, you can configure '
                 'well-known public DNS servers in individual network '
                 'connection settings.</p>', allow_markup=True)),
            ('opportunistic',
             format_lazy(
                 'Opportunistic. <p class="help-block">Encrypt connections to '
                 'the DNS server if the server supports DNS-over-TLS. '
                 'Otherwise, use unencrypted connections. There is no '
                 'protection against response manipulation.</p>',
                 allow_markup=True)),
            ('no',
             format_lazy(
                 'No. <p class="help-block">Do not encrypt domain name '
                 'resolutions.</p>', allow_markup=True)),
        ], initial='no')
