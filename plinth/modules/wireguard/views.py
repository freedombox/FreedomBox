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
Views for WireGuard application.
"""

import json

from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import FormView

import plinth.modules.wireguard as wireguard
from plinth import actions
from plinth.views import AppView

from . import forms


class WireguardView(AppView):
    """Serve configuration page."""
    app_id = 'wireguard'
    clients = wireguard.clients
    name = wireguard.name
    description = wireguard.description
    diagnostics_module_name = 'wireguard'
    show_status_block = False
    template_name = 'wireguard.html'
    port_forwarding_info = wireguard.port_forwarding_info

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        clients_list = actions.superuser_run('wireguard', ['list-clients'])
        context['server_clients'] = json.loads(clients_list)
        return context


class AddClientView(SuccessMessageMixin, FormView):
    """View to add a client."""
    form_class = forms.AddClientForm
    template_name = 'wireguard_add_client.html'
    success_url = reverse_lazy('wireguard:index')
    success_message = _('Added new client.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Client')
        return context

    def form_valid(self, form):
        """Add the client."""
        public_key = form.cleaned_data.get('public_key')
        actions.superuser_run(
            'wireguard', ['add-client', public_key])
        return super().form_valid(form)
