#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for configuring Shadowsocks.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ServiceForm

METHODS = ['chacha20-ietf-poly1305', 'aes-256-gcm']


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""

    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ShadowsocksForm(ServiceForm):
    """Shadowsocks configuration form"""
    server = TrimmedCharField(
        label=_('Server'),
        help_text=_('Server hostname or IP address'))

    server_port = forms.IntegerField(
        label=_('Server port'),
        min_value=0,
        max_value=65535,
        help_text=_('Server port number'))

    password = forms.CharField(
        label=_('Password'),
        help_text=_('Password used to encrypt data. '
                    'Must match server password.'))

    method = forms.ChoiceField(
        label=_('Method'),
        choices=[(method, method) for method in METHODS],
        help_text=_('Encryption method. Must match setting on server.'))
