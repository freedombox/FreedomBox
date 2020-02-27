# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring OpenVPN.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class OpenVpnForm(forms.Form):  # pylint: disable=W0232
    """OpenVPN configuration form."""
    enabled = forms.BooleanField(label=_('Enable OpenVPN server'),
                                 required=False)
