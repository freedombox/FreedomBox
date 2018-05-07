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
FreedomBox app for configuring MediaWiki.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ServiceForm


class MediaWikiForm(ServiceForm):  # pylint: disable=W0232
    """MediaWiki configuration form."""
    password = forms.CharField(
        label=_('Administrator Password'), help_text=_(
            'Set a new password for MediaWiki\'s administrator account '
            '(admin). Leave this field blank to keep the current password.'),
        required=False, widget=forms.PasswordInput)

    enable_public_registrations = forms.BooleanField(
        label=_('Enable public registrations'), required=False, help_text=_(
            'If enabled, anyone on the internet will be able to '
            'create an account on your MediaWiki instance.'))
