# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring Tor Proxy.
"""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.modules.tor.forms import TorCommonForm


class TorProxyForm(TorCommonForm):
    """Tor Proxy configuration form."""
    apt_transport_tor_enabled = forms.BooleanField(
        label=_('Download software packages over Tor'), required=False,
        help_text=_('When enabled, software will be downloaded over the Tor '
                    'network for installations and upgrades. This adds a '
                    'degree of privacy and security during software '
                    'downloads.'))
