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

from django import forms
from django.core import validators
from gettext import gettext as _

from plinth import network
from gi.repository import NM as nm

DEFAULT_SELECT_MSG = 'please select'


class ConnectionTypeSelectForm(forms.Form):
    """Form to select type for new connection."""
    connection_type = forms.ChoiceField(
        label=_('Connection Type'),
        choices=[(key, value)
                 for key, value in network.CONNECTION_TYPE_NAMES.items()])


class AddEthernetForm(forms.Form):
    """Form to create a new ethernet connection."""
    interfaces = network.get_interface_list(nm.DeviceType.ETHERNET)
    interfaces_list = (('', DEFAULT_SELECT_MSG), )
    for interface, mac in interfaces.items():
        displaystring = str(interface + ' (' + mac + ')')
        newentry = interfaces_list + ((interface, displaystring), )
        interfaces_list = newentry

    name = forms.CharField(label=_('Connection Name'))
    interface = forms.ChoiceField(
        label=_('Physical Interface'),
        choices=interfaces_list)
    zone = forms.ChoiceField(
        label=_('Firewall Zone'),
        help_text=_('The firewall zone will control which services are \
available over this interfaces. Select Internal only for trusted networks.'),
        choices=[('external', 'External'), ('internal', 'Internal')])
    ipv4_method = forms.ChoiceField(
        label=_('IPv4 Addressing Method'),
        choices=[('auto', 'Automatic (DHCP)'),
                 ('shared', 'Shared'),
                 ('manual', 'Manual')])
    ipv4_address = forms.CharField(
        label=_('Address'),
        validators=[validators.validate_ipv4_address],
        required=False)


class AddWifiForm(forms.Form):
    """Form to create a new wifi connection."""
    interfaces = network.get_interface_list(nm.DeviceType.WIFI)
    list_index = 1
    interfaces_list = ((list_index, DEFAULT_SELECT_MSG), )
    for interface, mac in interfaces.items():
        list_index += 1
        newentry = interfaces_list + ((list_index, interface), )
        interfaces_list = newentry

    name = forms.CharField(label=_('Connection Name'))
    interface = forms.ChoiceField(
        label=_('Physical interface'),
        choices=interfaces_list)
    zone = forms.ChoiceField(
        label=_('Firewall Zone'),
        help_text=_('The firewall zone will control which services are \
available over this interfaces. Select Internal only for trusted networks.'),
        choices=[('external', 'External'), ('internal', 'Internal')])
    ssid = forms.CharField(
        label=_('SSID'),
        help_text=_('The visible name of the network.'))
    mode = forms.ChoiceField(
        label=_('Mode'),
        choices=[('infrastructure', 'Infrastructure'),
                 ('ap', 'Access Point'),
                 ('adhoc', 'Ad-hoc')])
    auth_mode = forms.ChoiceField(
        label=_('Authentication Mode'),
        help_text=_('Select WPA if the wireless network is secured and \
requires clients to have the password to connect.'),
        choices=[('wpa', 'WPA'), ('open', 'Open')])
    passphrase = forms.CharField(
        label=_('Passphrase'),
        validators=[validators.MinLengthValidator(8)],
        required=False)
    ipv4_method = forms.ChoiceField(
        label=_('IPv4 Addressing Method'),
        choices=[('auto', 'Automatic (DHCP)'),
                 ('shared', 'Shared'),
                 ('manual', 'Manual')],
        help_text=_('Select Automatic (DHCP) if you are connecting to an \
existing wireless network. Shared mode is useful when running an Access \
Point.'))
    ipv4_address = forms.CharField(
        label=_('Address'),
        validators=[validators.validate_ipv4_address],
        required=False)
