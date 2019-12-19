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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Mumble server configuration form
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm


class MumbleForm(AppForm):
    """Mumble server configuration"""
    super_user_password = forms.CharField(
        max_length=20,
        label=_('Set SuperUser Password'),
        widget=forms.PasswordInput,
        help_text=_(
            'Optional. Leave this field blank to keep the current password. '
            'SuperUser password can be used to manage permissions in Mumble.'
        ),
        required=False,
    )
