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

from plinth.forms import ServiceForm


class MediawikiForm(ServiceForm):  # pylint: disable=W0232
    """Mediawiki configuration form"""
    password = forms.CharField(label=_('Administrator Password'), help_text=_(
        'Set a new password for Mediawiki\'s administrator account (admin)'),
                               widget=forms.PasswordInput)
