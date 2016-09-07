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
Forms for the tinc module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class TincSetupForm(forms.Form):
    """Form to complete tinc setup."""
    name = forms.CharField(
        label=_('Name'),
        help_text=_('Your hostname on the VPN'))

    ip = forms.CharField(
        label=_('IP Address'),
        help_text=_('Your new IP address on the VPN. It should begin with '
                    '10. or 198.162. or 17.16.'))

    address = forms.CharField(
        label=_('Address'),
        required=False,
        help_text=_('Optional, an IP address or domain name where your tinc '
                    'can be accessed (over the public Internet)'))


class TincForm(forms.Form):
    """Form to configure tinc after setup."""
    enabled = forms.BooleanField(
        label=_('Enable tinc'),
        required=False)
