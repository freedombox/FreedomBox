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
Plinth module for configuring Monkeysphere.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


class MonkeysphereAuthForm(forms.Form):
    """Monkeysphere authentication form."""
    enabled = forms.BooleanField(
        label=_('Enable web authentication using Monkeysphere'),
        required=False)


class MonkeysphereAuthAddForm(forms.Form):
    """Monkeysphere authentication form to add certifiers."""
    fingerprint = forms.RegexField(
        label=_('OpenPGP Fingerprint'),
        help_text=_('Fingerprint of an OpenPGP key that will be used to '
                    'validate client keys. Example: '
                    '1DEA112EDC105EDC0FEEDEC1A551F1ED1D0112ED'),
        regex=r'^\s*[A-Fa-f0-9]{40}\s*$',
        required=True)
