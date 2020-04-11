# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring diaspora*
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class DiasporaAppForm(forms.Form):
    """Service Form with additional fields for diaspora*"""
    is_user_registrations_enabled = forms.BooleanField(
        label=_('Enable new user registrations'), required=False)
