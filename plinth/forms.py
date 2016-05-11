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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Common forms for use by modules.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _


# TODO: remove this form once owncloud is removed (it's the last using it).
class ConfigurationForm(forms.Form):
    """Generic configuration form for simple modules."""
    enabled = forms.BooleanField(
        label=_('Enable application'),
        required=False)


class ServiceForm(forms.Form):
    """Generic configuration form for a service."""
    is_enabled = forms.BooleanField(
        label=_('Enable application'),
        required=False)
