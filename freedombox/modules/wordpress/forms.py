# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring WordPress.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class WordPressForm(forms.Form):
    """WordPress configuration form"""

    is_public = forms.BooleanField(
        label=_('Public access'), required=False, help_text=_(
            'Allow all visitors. Disabling allows only administrators to view '
            'the WordPress site or blog. Enable only after performing initial '
            'WordPress setup.'))
