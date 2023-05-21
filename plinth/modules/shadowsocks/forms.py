# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring Shadowsocks Client."""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.modules.shadowsocksserver.forms import METHODS


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField."""

    def clean(self, value):
        """Clean and validate the field value."""
        if value:
            value = value.strip()

        return super().clean(value)


class ShadowsocksForm(forms.Form):
    """Shadowsocks Client configuration form."""

    server = TrimmedCharField(label=_('Server'),
                              help_text=_('Server hostname or IP address'))

    server_port = forms.IntegerField(label=_('Server port'), min_value=0,
                                     max_value=65535,
                                     help_text=_('Server port number'))

    password = forms.CharField(
        label=_('Password'), help_text=_('Password used to encrypt data. '
                                         'Must match server password.'))

    method = forms.ChoiceField(
        label=_('Method'), choices=METHODS,
        help_text=_('Encryption method. Must match setting on server.'))
