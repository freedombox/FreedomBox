# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for the Single Sign On app of FreedomBox.
"""

from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.forms import \
    AuthenticationForm as DjangoAuthenticationForm
from django.utils.translation import gettext_lazy as _


class AuthenticationForm(DjangoAuthenticationForm):
    """Authentication form with an additional username field attributes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'autofocus': 'autofocus',
            'autocapitalize': 'none',
            'autocomplete': 'username'
        })


class CaptchaForm(forms.Form):
    """Form with a CAPTCHA field to use after 3 invalid login attempts."""
    captcha = CaptchaField(
        label=_('Enter the letters in the image to proceed to the login page'))
