# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the Single Sign On app of FreedomBox.
"""

from captcha.fields import CaptchaField
from django.contrib.auth.forms import \
    AuthenticationForm as DjangoAuthenticationForm


class AuthenticationForm(DjangoAuthenticationForm):
    """Authentication form with an additional username field attributes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocapitalize': 'none',
            'autocomplete': 'username'
        })


class CaptchaAuthenticationForm(AuthenticationForm):
    """Authentication form with an additional Captcha field."""
    captcha = CaptchaField()
