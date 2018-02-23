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
Plinth views for Searx.
"""

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.errors import ActionError
from plinth.modules.searx import clients, description, get_safe_search_setting

from .forms import SearxForm


class SearxServiceView(views.ServiceView):
    """Serve configuration page."""
    clients = clients
    description = description
    diagnostics_module_name = 'searx'
    service_id = 'searx'
    form_class = SearxForm
    show_status_block = False

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        initial['safe_search'] = get_safe_search_setting()
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        form_data = form.cleaned_data

        if form_data['safe_search']:
            try:
                actions.superuser_run(
                    'searx',
                    ['set-safe-search',
                     str(form_data['safe_search'])])
                messages.success(self.request,
                                 _('Safe search setting updated'))
            except ActionError as e:
                messages.error(self.request,
                               _('Failed to update safe search setting'))

        return super().form_valid(form)
