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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Plinth form for configuring Coquelicot.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm


class CoquelicotForm(AppForm):  # pylint: disable=W0232
    """Coquelicot configuration form."""
    upload_password = forms.CharField(
        label=_('Upload Password'),
        help_text=_('Set a new upload password for Coquelicot. '
                    'Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput)
    max_file_size = forms.IntegerField(
        label=_("Maximum File Size (in MiB)"), help_text=_(
            'Set the maximum size of the files that can be uploaded to '
            'Coquelicot.'), required=False, min_value=0)
