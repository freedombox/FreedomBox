# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring Zoph.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class ZophForm(forms.Form):
    """Zoph application configuration form."""

    enable_osm = forms.BooleanField(
        label=_('Enable OpenStreetMap for maps'), required=False,
        help_text=_('When enabled, requests will be made to OpenStreetMap '
                    'servers from user\'s browser. This impacts privacy.'))
