# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox privacy app."""

from django import forms
from django.core import validators
from django.utils.translation import gettext_lazy as _

from plinth import cfg
from plinth.modules import names
from plinth.utils import format_lazy


class PrivacyForm(forms.Form):
    """Privacy configuration form."""

    help_ip_lookup_url = format_lazy(
        _('Optional Value. This URL is used to determine the publicly visible '
          'IP address of your {box_name}. The URL should simply return the '
          'IPv4 or IPv6 address where the client request comes from. Default '
          'is to use the service provided by the FreedomBox Foundation at '
          'https://ddns.freedombox.org/ip/. If empty, lookups are disabled '
          'and some functionality will fail.'), box_name=_(cfg.box_name))

    enable_popcon = forms.BooleanField(
        label=_('Periodically submit a list of apps used (suggested)'),
        required=False, help_text=format_lazy(
            _('Help Debian/{box_name} developers by participating in the '
              'Popularity Contest package survey program. When enabled, a '
              'list of apps used on this system will be anonymously submitted '
              'to Debian every week. Statistics for the data collected are '
              'publicly available at <a href="https://popcon.debian.org/" '
              'target="_blank">popcon.debian.org</a>. Submission happens over '
              'the Tor network for additional anonymity if Tor app is enabled.'
              ), box_name=_(cfg.box_name)))

    dns_fallback = forms.BooleanField(
        label=_('Allow using fallback DNS servers'), required=False,
        help_text=_(
            'Use well-known public DNS servers to resolve domain names in '
            'unusual circumstances where no DNS servers are known but '
            'internet connectivity is available. Can be disabled in most '
            'cases if network connectivity is stable and reliable.'))

    ip_lookup_url = forms.CharField(
        label=_('URL to look up public IP address'), required=False,
        help_text=help_ip_lookup_url,
        validators=[validators.URLValidator(schemes=['http', 'https'])])

    def __init__(self, *args, **kwargs):
        """Disable DNS fallback field if necessary."""
        super().__init__(*args, **kwargs)
        self.fields['dns_fallback'].disabled = (
            not names.is_resolved_installed())
