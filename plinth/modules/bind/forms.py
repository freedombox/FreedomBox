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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Forms for BIND module.
"""

from django import forms
from django.core.validators import validate_ipv46_address
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ServiceForm


def validate_ips(ips):
    """Validate that ips is a list of IP addresses, separated by space."""
    for ip_addr in ips.split():
        validate_ipv46_address(ip_addr)


class BindForm(ServiceForm):
    """BIND configuration form"""
    set_forwarding = forms.BooleanField(
        label=_('Enable forwarding'),
        required=False,
        help_text=_('Enable forwarding on your BIND server'))

    enable_dnssec = forms.BooleanField(
        label=_('Enable DNSSEC'),
        required=False,
        help_text=_('Enable Domain Name System Security Extensions'))

    forwarders = forms.CharField(
        required=False,
        validators=[validate_ips],
        help_text=_('A list of IP addresses, separated by space'))
