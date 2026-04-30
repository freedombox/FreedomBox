# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for wireguard module.
"""

import base64
import binascii
import ipaddress

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

KEY_LENGTH = 32


def validate_key(key):
    """Validate a WireGuard public/private/pre-shared key."""
    valid = False
    if isinstance(key, str):
        key = key.encode()

    try:
        decoded_key = base64.b64decode(key)
        if len(decoded_key) == KEY_LENGTH and base64.b64encode(
                decoded_key) == key:
            valid = True
    except binascii.Error:
        pass

    if not valid:
        raise ValidationError(_('Invalid key.'))


def validate_endpoint(endpoint):
    """Validate an endpoint of the form: demo.wireguard.com:12912.

    Implemented similar to nm-utils.c::_parse_endpoint().

    """
    valid = False
    try:
        destination, port = endpoint.rsplit(':', maxsplit=1)
        port = int(port)
        if 1 <= port < ((1 << 16) - 1) and destination:
            valid = True

        if destination[0] == '[' and (destination[-1] != ']'
                                      or len(destination) < 3):
            valid = False
    except ValueError:
        pass

    if not valid:
        raise ValidationError('Invalid endpoint.')


def validate_ip_address_with_network(value: str):
    """Check that value is a valid IP address with an optional network."""
    try:
        ipaddress.ip_interface(value)
    except ValueError:
        raise ValidationError(_('Not a valid IP address.'))


class AddClientForm(forms.Form):
    """Form to add client."""
    public_key = forms.CharField(
        label=_('Public Key'), strip=True,
        help_text=_('Public key of the peer. Example: '
                    'MConEJFIg6+DFHg2J1nn9SNLOSE9KR0ysdPgmPjibEs= .'),
        validators=[validate_key])


class AutoAddClientForm(forms.Form):
    """Empty form for auto-client addition UX."""
    pass


class AddServerForm(forms.Form):
    """Form to add server."""
    peer_endpoint = forms.CharField(
        label=_('Endpoint of the server'), strip=True,
        help_text=_('Domain name and port in the form "ip:port". Example: '
                    'demo.wireguard.com:12912 .'),
        validators=[validate_endpoint])

    peer_public_key = forms.CharField(
        label=_('Public key of the server'), strip=True, help_text=_(
            'Provided by the server operator, a long string of characters. '
            'Example: MConEJFIg6+DFHg2J1nn9SNLOSE9KR0ysdPgmPjibEs= .'),
        validators=[validate_key])

    ip_address_and_network = forms.CharField(
        label=_('Client IP address provided by server'), strip=True,
        help_text=_(
            'IP address assigned to this machine on the VPN after connecting '
            'to the endpoint. This value is usually provided by the server '
            'operator. Example: 192.168.0.10 or '
            '2a03:7c80:4b2c:91a2:5d41:ffee:9b82:7c17. You can also specify '
            'the network. This will allow reaching machines in the network. '
            'Examples: 10.68.12.43/24 or 10.68.12.43/255.255.255.0.'),
        validators=[validate_ip_address_with_network])

    private_key = forms.CharField(
        label=_('Private key of this machine'), strip=True, help_text=_(
            'Optional. New public/private keys are generated if left blank. '
            'Public key can then be provided to the server. This is the '
            'recommended way. However, some server operators insist on '
            'providing this. Example: '
            'MConEJFIg6+DFHg2J1nn9SNLOSE9KR0ysdPgmPjibEs= .'), required=False,
        validators=[validate_key])

    preshared_key = forms.CharField(
        label=_('Pre-shared key'), strip=True, required=False, help_text=_(
            'Optional. A shared secret key provided by the server to add an '
            'additional layer of security. Fill in only if provided. Example: '
            'MConEJFIg6+DFHg2J1nn9SNLOSE9KR0ysdPgmPjibEs=.'),
        validators=[validate_key])

    default_route = forms.BooleanField(
        label=_('Use this connection to send all outgoing traffic'),
        required=False, help_text=_(
            'Typically checked for a VPN service through which all traffic '
            'is sent.'))

    def _build_ipv4_settings(self, iface) -> dict:
        """Build IPv4 NM settings from interfaces."""
        return {
                'method': 'manual',
                'address': str(iface.ip),
                'netmask': str(iface.netmask),
                'gateway': '',
                'dns': '',
                'second_dns': '',
                }

    def _build_ipv6_settings(self, iface) -> dict:
        """Build IPv6 NM settings from interfaces."""
        return {
                'method': 'manual',
                'address': str(iface.ip),
                'prefix': iface.network.prefixlen,
                'gateway': '',
                'dns': '',
                'second_dns': '',
                }

    def get_settings(self) -> dict[str, dict]:
        """Return NM settings dict from cleaned data."""
        ip_interface = ipaddress.ip_interface(
            self.cleaned_data['ip_address_and_network']
        )

        if self.cleaned_data['default_route']:
            allowed_ips = ['0.0.0.0/0', '::/0']
        else:
            allowed_ips = [str(ip_interface)]

        settings = {
            'common': {
                'type': 'wireguard',
                'zone': 'external',
            },
            'wireguard': {
                'peer_endpoint': self.cleaned_data['peer_endpoint'],
                'peer_public_key': self.cleaned_data['peer_public_key'],
                'private_key': self.cleaned_data['private_key'],
                'preshared_key': self.cleaned_data['preshared_key'],
                'allowed_ips': allowed_ips,
            }
        }

        if ip_interface.version == 4:
            settings['ipv4'] = self._build_ipv4_settings(ip_interface)
        else:
            settings['ipv6'] = self._build_ipv6_settings(ip_interface)

        return settings
