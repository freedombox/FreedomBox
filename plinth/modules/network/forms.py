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
from gettext import gettext as _


CONNECTION_TYPE_NAMES = {
    '802-3-ethernet': 'Ethernet',
    '802-11-wireless': 'Wi-Fi',
}


class ConnectionTypeSelectForm(forms.Form):
    """Form to select type for new connection."""
    conn_type = forms.ChoiceField(
        label=_('Connection Type'),
        choices=[(k, v) for k, v in CONNECTION_TYPE_NAMES.items()])


class AddEthernetForm(forms.Form):
    """Form to create a new ethernet connection."""
    name = forms.CharField(label=_('Connection Name'))
    ipv4_method = forms.ChoiceField(
        label=_('IPv4 Addressing Method'),
        choices=[('auto', 'Automatic (DHCP)'), ('manual', 'Manual')])
    ipv4_address = forms.CharField(label=_('Address'), required=False)


class AddWifiForm(forms.Form):
    """Form to create a new wifi connection."""
    name = forms.CharField(label=_('Connection Name'))
    ssid = forms.CharField(label=_('SSID'))
    ipv4_method = forms.ChoiceField(
        label=_('IPv4 Addressing Method'),
        choices=[('auto', 'Automatic (DHCP)'), ('manual', 'Manual')])
    ipv4_address = forms.CharField(label=_('Address'), required=False)
