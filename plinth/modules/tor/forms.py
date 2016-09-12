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

from plinth import cfg
from plinth.utils import format_lazy


BRIDGE_VALIDATION_ERROR_MESSAGE = _('Enter a valid bridge with this format: '
                                    '[transport] IP:ORPort [fingerprint]')


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


def bridges_validator(bridges):
    """Validate upstream bridges entries."""
    for bridge in bridges.split('\n'):
        parts = bridge.split()

        # IP:ORPort is required, transport and fingerprint are optional.
        if len(parts) < 1 or len(parts) > 3:
            raise ValidationError(
                BRIDGE_VALIDATION_ERROR_MESSAGE, code='invalid')

        # May start with transport or IP:ORPort.
        try:
            ip_info = parts[0].split(':')
            validate_ipv46_address(ip_info[0])
        except ValidationError:
            try:
                ip_info = parts[1].split(':')
                validate_ipv46_address(ip_info[0])
            except ValidationError:
                raise ValidationError(
                    BRIDGE_VALIDATION_ERROR_MESSAGE, code='invalid')

        try:
            port = int(ip_info[1])
        except ValueError:
            raise ValidationError(
                BRIDGE_VALIDATION_ERROR_MESSAGE, code='invalid')
        if port < 0 or port > 65535:
            raise ValidationError(
                BRIDGE_VALIDATION_ERROR_MESSAGE, code='invalid')


class TorForm(forms.Form):  # pylint: disable=W0232
    """Tor configuration form."""
    enabled = forms.BooleanField(
        label=_('Enable Tor'),
        required=False)
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
    use_upstream_bridges = forms.BooleanField(
        label=_('Use upstream bridges to connect to Tor network'),
        required=False,
        help_text=_('When enabled, the bridges configured below will be used '
                    'to connect to the Tor network. This will disable relay '
                    'modes. Use this option only if you cannot connect to '
                    'the Tor network directly.'))
    upstream_bridges = TrimmedCharField(
        widget=widgets.Textarea,
        label=_('Upstream bridges'),
        required=False,
        help_text=_('If you need to use a bridge to connect to Tor network, '
                    'you can get some bridges from '
                    'https://bridges.torproject.org/ and paste the bridge '
                    'information here.'),
        validators=[bridges_validator])
