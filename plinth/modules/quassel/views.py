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

from plinth.modules import quassel
from plinth.views import AppView

from .forms import QuasselForm


class QuasselAppView(AppView):
    app_id = 'quassel'
    diagnostics_module_name = 'quassel'
    name = quassel.name
    description = quassel.description
    clients = quassel.clients
    manual_page = quassel.manual_page
    port_forwarding_info = quassel.port_forwarding_info
    form_class = QuasselForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = quassel.get_domain()
        return initial

    def form_valid(self, form):
        """Change the access control of Radicale service."""
        data = form.cleaned_data
        if quassel.get_domain() != data['domain']:
            quassel.set_domain(data['domain'])
            quassel.app.get_component(
                'letsencrypt-quassel').setup_certificates()

        return super().form_valid(form)
