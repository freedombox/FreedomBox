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
Views for radicale module.
"""

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.modules import radicale
from plinth.views import AppView

from . import description, get_rights_value
from .forms import RadicaleForm


class RadicaleAppView(AppView):
    """A specialized view for configuring radicale service."""
    clients = radicale.clients
    name = radicale.name
    description = description
    form_class = RadicaleForm
    app_id = 'radicale'
    manual_page = radicale.manual_page
    icon_filename = radicale.icon_filename

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['access_rights'] = get_rights_value()
        return initial

    def form_valid(self, form):
        """Change the access control of Radicale service."""
        data = form.cleaned_data
        if get_rights_value() != data['access_rights']:
            actions.superuser_run(
                'radicale',
                ['configure', '--rights_type', data['access_rights']])
            messages.success(self.request,
                             _('Access rights configuration updated'))
        return super().form_valid(form)
