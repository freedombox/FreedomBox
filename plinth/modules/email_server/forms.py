# SPDX-License-Identifier: AGPL-3.0-or-later
from django import forms
from django.utils.translation import ugettext_lazy as _


class EmailServerForm(forms.Form):
    domain = forms.CharField(label=_('domain'), max_length=256)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class AliasCreationForm(forms.Form):
    email_name = forms.CharField(label=_('New alias (without @domain)'),
                                 max_length=50)


class MailnameForm(forms.Form):
    mailname = forms.CharField(label=_('New value'), max_length=256)


class MydomainForm(forms.Form):
    mydomain = forms.CharField(label=_('New value'), max_length=256)


class MydestinationForm(forms.Form):
    mydestination = forms.CharField(label=_('New value'), max_length=4000)
