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
Forms for the Matrix Synapse module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm


class MatrixSynapseForm(AppForm):
    enable_public_registration = forms.BooleanField(
        label=_('Enable Public Registration'), required=False, help_text=_(
            'Enabling public registration means that anyone on the Internet '
            'can register a new account on your Matrix server. Disable this '
            'if you only want existing users to be able to use it.'))
