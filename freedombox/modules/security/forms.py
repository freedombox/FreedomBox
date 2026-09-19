# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for security module
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class SecurityForm(forms.Form):
    """Security configuration form"""
    fail2ban_enabled = forms.BooleanField(
        label=_('Fail2Ban (recommended)'), required=False,
        help_text=_('When this option is enabled, Fail2Ban will limit '
                    'brute force break-in attempts to the SSH server and '
                    'other enabled password protected internet-services.'))
