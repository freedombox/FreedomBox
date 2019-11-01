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

import urllib.parse

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import FormView, TemplateView

import plinth.modules.wireguard as wireguard
from plinth import actions, network
from plinth.views import AppView

from . import forms, utils


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

        public_key = urllib.parse.unquote(self.kwargs['public_key'])
        info = wireguard.get_info()
        context.update(info)
        for client in info['my_server']['clients']:
            if client['public_key'] == public_key:
                context['client'] = client

        return context


class EditClientView(SuccessMessageMixin, FormView):
    """View to modify a client."""
    form_class = forms.AddClientForm
    template_name = 'wireguard_edit_client.html'
    success_url = reverse_lazy('wireguard:index')
    success_message = _('Updated client.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modify Client')
        return context

    def get_initial(self):
        """Get initial form data."""
        initial = super().get_initial()
        initial['public_key'] = urllib.parse.unquote(self.kwargs['public_key'])
        return initial

    def form_valid(self, form):
        """Update the client."""
        old_public_key = form.initial['public_key']
        actions.superuser_run('wireguard', ['remove-client', old_public_key])

        public_key = form.cleaned_data.get('public_key')
        actions.superuser_run('wireguard', ['add-client', public_key])
        return super().form_valid(form)


class DeleteClientView(SuccessMessageMixin, TemplateView):
    """View to delete a client."""
    template_name = 'wireguard_delete_client.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Client')
        context['public_key'] = urllib.parse.unquote(self.kwargs['public_key'])
        return context

    def post(self, request, public_key):
        """Delete the client."""
        public_key = urllib.parse.unquote(public_key)
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
        utils.add_server(form.get_settings())
        return super().form_valid(form)


class ShowServerView(SuccessMessageMixin, TemplateView):
    """View to show a server's details."""
    template_name = 'wireguard_show_server.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Server Information')

        interface = self.kwargs['interface']
        info = wireguard.get_info()
        server = info['my_client']['servers'].get(interface)
        if not server:
            raise Http404

        context['interface'] = interface
        context['server'] = server
        return context


class EditServerView(SuccessMessageMixin, FormView):
    """View to modify a server."""
    form_class = forms.AddServerForm
    template_name = 'wireguard_edit_server.html'
    success_url = reverse_lazy('wireguard:index')
    success_message = _('Updated server.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Modify Server')
        return context

    def get_initial(self):
        """Get initial form data."""
        initial = super().get_initial()
        interface = self.kwargs['interface']
        info = wireguard.get_nm_info()
        server = info.get(interface)
        if not server:
            raise Http404

        initial['ip_address'] = server.get('ip_address')
        if server['peers']:
            peer = server['peers'][0]
            initial['peer_endpoint'] = peer['endpoint']
            initial['peer_public_key'] = peer['public_key']
            initial['private_key'] = server['private_key']
            initial['preshared_key'] = peer['preshared_key']
            initial['default_route'] = server['default_route']

        return initial

    def form_valid(self, form):
        """Update the server."""
        settings = form.get_settings()
        interface = self.kwargs['interface']
        settings['common']['interface'] = interface
        settings['common']['name'] = 'WireGuard-' + interface
        connection = network.get_connection_by_interface_name(interface)
        network.edit_connection(connection, settings)
        return super().form_valid(form)


class DeleteServerView(SuccessMessageMixin, TemplateView):
    """View to delete a server."""
    template_name = 'wireguard_delete_server.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Server')

        interface = self.kwargs['interface']
        info = wireguard.get_nm_info()
        server = info.get(interface)
        if not server:
            raise Http404

        context['interface'] = interface
        if server['peers']:
            peer = server['peers'][0]
            context['peer_endpoint'] = peer['endpoint']
            context['peer_public_key'] = peer['public_key']

        return context

    def post(self, request, interface):
        """Delete the server."""
        connection = network.get_connection_by_interface_name(interface)
        network.delete_connection(connection.get_uuid())
        messages.success(request, _('Server deleted.'))
        return redirect('wireguard:index')
