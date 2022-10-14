# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring Shadowsocks."""

from django import forms
from django.utils.translation import gettext_lazy as _

from plinth.utils import format_lazy

METHODS = [('chacha20-ietf-poly1305',
            format_lazy('chacha20-ietf-poly1305 ({})', _('Recommended'))),
           ('aes-256-gcm', format_lazy('aes-256-gcm ({})', _('Recommended'))),
           ('aes-192-gcm', 'aes-192-gcm'), ('aes-128-gcm', 'aes-128-gcm'),
           ('aes-128-ctr', 'aes-128-ctr'), ('aes-192-ctr', 'aes-192-ctr'),
           ('aes-256-ctr', 'aes-256-ctr'), ('aes-128-cfb', 'aes-128-cfb'),
           ('aes-192-cfb', 'aes-192-cfb'), ('aes-256-cfb', 'aes-256-cfb'),
           ('camellia-128-cfb', 'camellia-128-cfb'),
           ('camellia-192-cfb', 'camellia-192-cfb'),
           ('camellia-256-cfb', 'camellia-256-cfb'),
           ('chacha20-ietf', 'chacha20-ietf')]


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField."""

    def clean(self, value):
        """Clean and validate the field value."""
        if value:
            value = value.strip()

        return super().clean(value)


class ShadowsocksForm(forms.Form):
    """Shadowsocks configuration form."""

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
