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
Forms for configuring ikiwiki
"""

from django import forms
from gettext import gettext as _


class IkiwikiForm(forms.Form):
    """ikiwiki configuration form."""
    enabled = forms.BooleanField(
        label=_('Enable Ikiwiki'),
        required=False)


class IkiwikiCreateForm(forms.Form):
    """Form to create a wiki or blog."""
    site_type = forms.ChoiceField(
        label=_('Type'),
        choices=[('wiki', 'Wiki'), ('blog', 'Blog')])

    name = forms.CharField(label=_('Name'))

    admin_name = forms.CharField(label=_('Admin Account Name'))

    admin_password = forms.CharField(
        label=_('Admin Account Password'),
        widget=forms.PasswordInput())
