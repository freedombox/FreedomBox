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
Forms for Quassel app.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import AppForm
from plinth.modules import quassel


def get_domain_choices():
    """Double domain entries for inclusion in the choice field."""
    return ((domain, domain) for domain in quassel.get_available_domains())


class QuasselForm(AppForm):
    """Form to select a TLS domain for Quassel."""

    domain = forms.ChoiceField(
        choices=get_domain_choices,
        label=_('TLS domain'),
        help_text=_(
            'Select a domain to use TLS with. If the list is empty, please '
            'configure at least one domain with certificates.'),
    )
