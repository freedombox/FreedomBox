# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from django.utils.translation import gettext_lazy as _


class EmailServerForm(forms.Form):
    domain = forms.CharField(label=_('domain'), max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AliasCreationForm(forms.Form):
    email_name = forms.CharField(label=_('New alias (without @domain)'),
                                 max_length=50)
