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

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import FormView, TemplateView

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
        context['public_key'] = wireguard.get_public_key()
        info = wireguard.get_info()
        context['server_peers'] = info['my_server']['clients']
        context['client_peers'] = info['my_client']['servers']
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
        actions.superuser_run('wireguard', ['add-client', public_key])
        return super().form_valid(form)


class ShowClientView(SuccessMessageMixin, TemplateView):
    """View to show a client's details."""
    template_name = 'wireguard_show_client.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Show Client')

        public_key = self.kwargs['public_key']
        info = wireguard.get_info()
        context.update(info)
        for client in info['my_server']['clients']:
            if client['public_key'] == public_key:
                context['client'] = client

        return context


class DeleteClientView(SuccessMessageMixin, TemplateView):
    """View to delete a client."""
    template_name = 'wireguard_delete_client.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Client')
        context['public_key'] = self.kwargs['public_key']
        return context

    def post(self, request, public_key):
        """Delete the client."""
        actions.superuser_run('wireguard', ['remove-client', public_key])
        messages.success(request, _('Client deleted.'))
        return redirect('wireguard:index')


class AddServerView(SuccessMessageMixin, FormView):
    """View to add a server."""
    form_class = forms.AddServerForm
    template_name = 'wireguard_add_server.html'
    success_url = reverse_lazy('wireguard:index')
    success_message = _('Added new server.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Server')
        return context

    def form_valid(self, form):
        """Add the server."""
        endpoint = form.cleaned_data.get('endpoint')
        client_ip_address = form.cleaned_data.get('client_ip_address')
        public_key = form.cleaned_data.get('public_key')
        pre_shared_key = form.cleaned_data.get('pre_shared_key')
        all_outgoing_traffic = form.cleaned_data.get('all_outgoing_traffic')
        args = ['add-server', '--endpoint', endpoint, '--client-ip',
                client_ip_address, '--public-key', public_key]
        if pre_shared_key:
            # TODO: pass pre-shared key through stdin
            args += ['--pre-shared-key', pre_shared_key]

        if all_outgoing_traffic:
            args.append('--all-outgoing')

        actions.superuser_run('wireguard', args)
        return super().form_valid(form)


class ShowServerView(SuccessMessageMixin, TemplateView):
    """View to show a server's details."""
    template_name = 'wireguard_show_server.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Show Server')

        public_key = self.kwargs['public_key']
        info = wireguard.get_info()
        context.update(info)
        for server in info['my_client']['servers']:
            if server['public_key'] == public_key:
                context['server'] = server

        return context
