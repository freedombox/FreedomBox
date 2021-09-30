# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox configuration form for OpenSSH server.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class SSHServerForm(forms.Form):
    """SSH server configuration form."""
    password_auth_disabled = forms.BooleanField(
        label=_('Disable password authentication'),
        help_text=_('Improves security by preventing password guessing. '
                    'Ensure that you have setup SSH keys in your '
                    'administrator user account before enabling this option.'),
        required=False,
    )
