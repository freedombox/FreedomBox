# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for configuring ikiwiki
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class IkiwikiCreateForm(forms.Form):
    """Form to create a wiki or blog."""
    site_type = forms.ChoiceField(label=_('Type'), choices=[('wiki', 'Wiki'),
                                                            ('blog', 'Blog')])

    name = forms.CharField(label=_('Name'))

    admin_name = forms.CharField(label=_('Admin Account Name'))

    admin_password = forms.CharField(label=_('Admin Account Password'),
                                     widget=forms.PasswordInput())
