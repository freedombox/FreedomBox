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
    peer_endpoint = forms.CharField(
        label=_('Endpoint of the server'), strip=True,
        help_text=_('Domain name and port in the form "ip:port". Example: '
                    'demo.wireguard.com:12912 .'))

    peer_public_key = forms.CharField(
        label=_('Public key of the server'), strip=True, help_text=_(
            'Provided by the server operator, a long string of characters.'))

    ip_address = forms.CharField(
        label=_('Client IP address provided by server'), strip=True,
        help_text=_('IP address assigned to this machine on the VPN after '
                    'connecting to the endpoint. This value is usually '
                    'provided by the server operator. Example: 192.168.0.10.'))

    private_key = forms.CharField(
        label=_('Private key of this machine'), strip=True, help_text=_(
            'Optional. New public/private keys are generated if left blank. '
            'Public key can then be provided to the server. This is the '
            'recommended way. However, some server operators insist on '
            'providing this.'), required=False)

    preshared_key = forms.CharField(
        label=_('Pre-shared key'), strip=True, required=False, help_text=_(
            'Optional. A shared secret key provided by the server to add an '
            'additional layer of security. Fill in only if provided.'))

    default_route = forms.BooleanField(
        label=_('Use this connection to send all outgoing traffic'),
        required=False, help_text=_(
            'Typically checked for a VPN service though which all traffic '
            'is sent.'))

    def get_settings(self):
        """Return NM settings dict from cleaned data."""
        settings = {
            'common': {
                'type': 'wireguard',
                'zone': 'external',
            },
            'ipv4': {
                'method': 'manual',
                'address': self.cleaned_data['ip_address'],
                'netmask': '',
                'gateway': '',
                'dns': '',
                'second_dns': '',
            },
            'wireguard': {
                'peer_endpoint': self.cleaned_data['peer_endpoint'],
                'peer_public_key': self.cleaned_data['peer_public_key'],
                'private_key': self.cleaned_data['private_key'],
                'preshared_key': self.cleaned_data['preshared_key'],
                'default_route': self.cleaned_data['default_route'],
            }
        }
        return settings
