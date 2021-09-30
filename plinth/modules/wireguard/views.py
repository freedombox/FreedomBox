# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for WireGuard application.
"""

import urllib.parse

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import FormView, TemplateView

from plinth import network
from plinth.modules.names.components import DomainName
from plinth.views import AppView

from . import forms, utils


class WireguardView(AppView):
    """Serve configuration page."""
    app_id = 'wireguard'
    diagnostics_module_name = 'wireguard'
    template_name = 'wireguard.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        info = utils.get_info()
        context['server'] = info['my_server']
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
        context['title'] = _('Add Allowed Client')
        return context

    def form_valid(self, form):
        """Add the client."""
        public_key = form.cleaned_data.get('public_key')
        try:
            utils.add_client(public_key)
        except ValueError:
            messages.warning(self.request,
                             _('Client with public key already exists'))
            return redirect('wireguard:index')

        return super().form_valid(form)


class ShowClientView(SuccessMessageMixin, TemplateView):
    """View to show a client's details."""
    template_name = 'wireguard_show_client.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Allowed Client')

        public_key = urllib.parse.unquote(self.kwargs['public_key'])
        server_info = utils.get_info()['my_server']
        if not server_info or public_key not in server_info['peers']:
            raise Http404

        domains = DomainName.list_names(filter_for_service='wireguard')
        context['server'] = server_info
        context['client'] = server_info['peers'][public_key]
        context['endpoints'] = [
            domain + ':' + str(server_info['listen_port'])
            for domain in domains
        ]
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
        public_key = form.cleaned_data.get('public_key')

        if old_public_key != public_key:
            try:
                utils.add_client(public_key)
            except ValueError:
                messages.warning(self.request,
                                 _('Client with public key already exists'))

            utils.remove_client(old_public_key)

        return super().form_valid(form)


class DeleteClientView(SuccessMessageMixin, TemplateView):
    """View to delete a client."""
    template_name = 'wireguard_delete_client.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Allowed Client')
        context['public_key'] = urllib.parse.unquote(self.kwargs['public_key'])
        return context

    def post(self, request, public_key):
        """Delete the client."""
        public_key = urllib.parse.unquote(public_key)
        try:
            utils.remove_client(public_key)
            messages.success(request, _('Client deleted.'))
        except KeyError:
            messages.error(request, _('Client not found'))

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
        context['title'] = _('Add Connection to Server')
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
        context['title'] = _('Connection to Server')

        interface = self.kwargs['interface']
        info = utils.get_info()
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
        context['title'] = _('Modify Connection to Server')
        return context

    def get_initial(self):
        """Get initial form data."""
        initial = super().get_initial()
        interface = self.kwargs['interface']
        info = utils.get_nm_info()
        server = info.get(interface)
        if not server:
            raise Http404

        initial['ip_address'] = server.get('ip_address')
        if server['peers']:
            peer = next(peer for peer in server['peers'].values())
            initial['peer_endpoint'] = peer['endpoint']
            initial['peer_public_key'] = peer['public_key']
            initial['private_key'] = server['private_key']
            initial['preshared_key'] = peer['preshared_key']
            initial['default_route'] = server['default_route']

        return initial

    def form_valid(self, form):
        """Update the server."""
        interface = self.kwargs['interface']
        utils.edit_server(interface, form.get_settings())
        return super().form_valid(form)


class DeleteServerView(SuccessMessageMixin, TemplateView):
    """View to delete a server."""
    template_name = 'wireguard_delete_server.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Delete Connection to Server')

        interface = self.kwargs['interface']
        info = utils.get_nm_info()
        server = info.get(interface)
        if not server:
            raise Http404

        context['interface'] = interface
        if server['peers']:
            peer = next(peer for peer in server['peers'].values())
            context['peer_endpoint'] = peer['endpoint']
            context['peer_public_key'] = peer['public_key']

        return context

    def post(self, request, interface):
        """Delete the server."""
        connection = network.get_connection_by_interface_name(interface)
        network.delete_connection(connection.get_uuid())
        messages.success(request, _('Server deleted.'))
        return redirect('wireguard:index')
