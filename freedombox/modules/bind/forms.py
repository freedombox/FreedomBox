# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for BIND module."""

from django import forms
from django.core.validators import validate_ipv46_address
from django.utils.translation import gettext_lazy as _


def validate_ips(ips):
    """Validate that ips is a list of IP addresses, separated by space."""
    for ip_addr in ips.split():
        validate_ipv46_address(ip_addr)


class BindForm(forms.Form):
    """BIND configuration form."""

    forwarders = forms.CharField(
        label=_('Forwarders'), required=False, validators=[validate_ips],
        help_text=_('A list DNS servers, separated by space, to which '
                    'requests will be forwarded'))
