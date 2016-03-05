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
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ConfigurationForm


class TransmissionForm(ConfigurationForm):  # pylint: disable=W0232
    """Transmission configuration form"""
    download_dir = forms.CharField(
        label=_('Download directory'),
        help_text=_('Directory where downloads are saved.  If you change the \
default directory, ensure that the new directory exists and is writable by \
"debian-transmission" user.'))

    rpc_username = forms.CharField(
        label=_('Username'),
        help_text=_('Username to login to the web interface.'))

    rpc_password = forms.CharField(
        label=_('Password'),
        help_text=_('Password to login to the web interface.  Current \
password is shown in a hashed format.  To set a new password, enter the \
password in plain text.'))
