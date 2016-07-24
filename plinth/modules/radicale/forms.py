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
Forms for radicale module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ServiceForm

CHOICES = [
    ('owner_only', _('Only the owner of a calendar/addressbook can view or '
                     'make changes.')),
    ('owner_write', _('Any user can view any calendar/addressbook, but only '
                      'the owner can make changes.')),
    ('authenticated', _('Any user can view or make changes to any '
                        'calendar/addressbook.')),
]


class RadicaleForm(ServiceForm):
    """Specialized configuration form for radicale service."""
    access_rights = forms.ChoiceField(choices=CHOICES, required=True,
                                      widget=forms.RadioSelect())
