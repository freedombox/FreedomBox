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
Forms for configuring Tor.
"""

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_ipv46_address
from django.forms import widgets
from django.utils.translation import ugettext_lazy as _
import re

from plinth import cfg
from plinth.utils import format_lazy


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()
            value = value.replace('\r\n', '\n')

        return super(TrimmedCharField, self).clean(value)


def bridges_validator(bridges):
    """Validate upstream bridges entries."""
    validation_error = ValidationError(
        _('Enter a valid bridge with this format: '
          '[transport] IP:ORPort [fingerprint]'), code='invalid')

    bridges = [bridge.strip() for bridge in bridges.split('\n')]
    bridges = [bridge for bridge in bridges if bridge]
    if not bridges:
        raise validation_error

    for bridge in bridges:
        parts = [part for part in bridge.split() if part]

        # IP:ORPort is required, transport and fingerprint are optional.
        # Transports may have additional options after the fingerprint.
        try:
            ip_port_part = parts[0]
            if re.match('[a-z_][a-z0-9_]*', parts[0]):
                ip_port_part = parts[1]
        except IndexError:
            raise validation_error

        match = re.match('\[([a-fA-F0-9:]+)\](?::([0-9]+))?', ip_port_part)
        if match:
            ip_address = match.group(1)
            port = match.group(2)
        else:
            ip_parts = ip_port_part.rsplit(':', maxsplit=1)
            ip_address = ip_parts[0]
            port = ip_parts[1] if len(ip_parts) > 1 else None

        try:
            validate_ipv46_address(ip_address)
        except ValidationError:
            raise validation_error

        if port:
            port = int(port)
            if port < 0 or port > 65535:
                raise validation_error


class TorForm(forms.Form):  # pylint: disable=W0232
    """Tor configuration form."""
    enabled = forms.BooleanField(
        label=_('Enable Tor'),
        required=False)
    use_upstream_bridges = forms.BooleanField(
        label=_('Use upstream bridges to connect to Tor network'),
        required=False,
        help_text=_(
            'When enabled, the bridges configured below will be used to '
            'connect to the Tor network. Use this option if your Internet '
            'Service Provider (ISP) blocks or censors connections to the '
            'Tor Network. This will disable relay modes.'))
    upstream_bridges = TrimmedCharField(
        widget=widgets.Textarea,
        label=_('Upstream bridges'),
        required=False,
        help_text=_(
            'You can get some bridges from <a '
            'href="https://bridges.torproject.org/">'
            'https://bridges.torproject.org/</a> and copy/paste the bridge '
            'information here. Currently supported transports are none, '
            'obfs3, obfs4 and scamblesuit.'),
        validators=[bridges_validator])
    relay_enabled = forms.BooleanField(
        label=_('Enable Tor relay'),
        required=False,
        help_text=format_lazy(_(
            'When enabled, your {box_name} will run a Tor relay and donate '
            'bandwidth to the Tor network. Do this if you have more than '
            '2 megabits/s of upload and download bandwidth.'),
                              box_name=_(cfg.box_name)))
    bridge_relay_enabled = forms.BooleanField(
        label=_('Enable Tor bridge relay'),
        required=False,
        help_text=format_lazy(_(
            'When enabled, relay information is published in the Tor bridge '
            'database instead of public Tor relay database making it harder '
            'to censor this node. This helps others circumvent censorship.'),
                              box_name=_(cfg.box_name)))
    hs_enabled = forms.BooleanField(
        label=_('Enable Tor Hidden Service'),
        required=False,
        help_text=format_lazy(_(
            'A hidden service will allow {box_name} to provide selected '
            'services (such as wiki or chat) without revealing its '
            'location. Do not use this for strong anonymity yet.'),
                              box_name=_(cfg.box_name)))
    apt_transport_tor_enabled = forms.BooleanField(
        label=_('Download software packages over Tor'),
        required=False,
        help_text=_('When enabled, software will be downloaded over the Tor '
                    'network for installations and upgrades. This adds a '
                    'degree of privacy and security during software '
                    'downloads.'))

    def clean(self):
        """Validate the form for cross-field integrity."""
        cleaned_data = super().clean()
        use_upstream_bridges = cleaned_data.get('use_upstream_bridges')
        upstream_bridges = cleaned_data.get('upstream_bridges')

        if use_upstream_bridges and not upstream_bridges:
            self.add_error('upstream_bridges', ValidationError(_(
                'Specify at least one upstream bridge to use upstream '
                'bridges.'), code='invalid'))

        return cleaned_data
