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
Forms for configuring unattended-upgrades.
"""

from django import forms
from gettext import gettext as _


class ConfigureForm(forms.Form):
    """Configuration form to enable/disable automatic upgrades."""
    auto_upgrades_enabled = forms.BooleanField(
        label=_('Enable automatic upgrades'), required=False,
        help_text=_('When enabled, the unattended-upgrades program will be \
run once per day. It will attempt to perform any package upgrades that are \
available.'))
