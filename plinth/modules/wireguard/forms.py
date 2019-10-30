#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Forms for wireguard module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class AddClientForm(forms.Form):
    """Form to add client."""
    public_key = forms.CharField(
        label=_('Public Key'), strip=True,
        help_text=_('Public key of the peer.'))


class AddServerForm(forms.Form):
    """Form to add server."""
    endpoint = forms.CharField(
        label=_('Endpoint'), strip=True,
        help_text=_('Server endpoint with the form "ip:port".'))

    client_ip_address = forms.CharField(
        label=_('Client IP address provided by server'), strip=True,
        help_text=_('Client IP address provided by server.'))

    public_key = forms.CharField(
        label=_('Public key of the server'), strip=True,
        help_text=_('Public key of the server.'))

    client_private_key = forms.CharField(
        label=_('Private key of the client'), strip=True,
        help_text=_('Optional. A new key is generated if left blank.'),
        required=False)

    pre_shared_key = forms.CharField(
        label=_('Pre-shared key'), strip=True, required=False,
        help_text=_('Optional: a shared secret key provided by the server to '
                    'add an additional layer of encryption.'))

    all_outgoing_traffic = forms.BooleanField(
        label=_('Use this connection to send all outgoing traffic'),
        required=False,
        help_text=_('Use this connection to send all outgoing traffic.'))
