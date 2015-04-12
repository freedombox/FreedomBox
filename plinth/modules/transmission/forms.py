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
Plinth module for configuring Transmission.
"""

from django import forms
from django.core.validators import RegexValidator
from gettext import gettext as _
import re


ipv4_wildcard_re = r'(25[0-5]|2[0-4]\d|[0-1]?\d?\d)' \
    r'(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d|\*)){3}'

multiple_ips_re = re.compile(r'^({ipv4})(\s*,\s*{ipv4})*$'.format(ipv4=ipv4_wildcard_re))
ip_validator = RegexValidator(multiple_ips_re)


class TransmissionForm(forms.Form):  # pylint: disable=W0232
    """Tor configuration form"""
    enabled = forms.BooleanField(
        label=_('Enable Transmission daemon'),
        required=False)

    download_dir = forms.CharField(
        label=_('Download directory'),
        help_text=_('Directory where downloads are saved.  If you change the \
default directory, ensure that the new directory exists and is writable by \
"debian-tramission" user'))

    rpc_username = forms.CharField(
        label=_('Username'),
        help_text=_('Username to login to the web interface'))

    rpc_password = forms.CharField(
        label=_('Password'),
        help_text=_('Password to login to the web interface.  Current \
password is shown in a hashed format.  To set a new password, enter the \
password in plain text.'))

    rpc_whitelist = forms.CharField(
        label=_('IP addresses to allow'),
        validators=[ip_validator],
        help_text=_('A comma separated list of IP addresses that will be \
allowed to connect to the web interface.  IP addresses may use wild cards, \
such as 192.168.*.* .'))
