# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for name services.
"""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from plinth.modules import names
from plinth.signals import domain_added, domain_removed
from plinth.views import AppView

from . import components, privileged, resolved
from .forms import DomainAddForm, HostnameForm, NamesConfigurationForm

logger = logging.getLogger(__name__)


class NamesAppView(AppView):
    """Show names app main page."""

    app_id = 'names'
    template_name = 'names.html'
    prefix = 'names'
    form_class = NamesConfigurationForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        if names.is_resolved_installed():
            initial.update(privileged.get_resolved_configuration())

        return initial

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['status'] = get_status()
        context['resolved_installed'] = names.is_resolved_installed()
        if context['resolved_installed']:
            try:
                context['resolved_status'] = resolved.get_status()
            except Exception as exception:
                context['resolved_status_error'] = exception

        return context

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_data = form.initial
        form_data = form.cleaned_data

        changes = {}
        if old_data['dns_over_tls'] != form_data['dns_over_tls']:
            changes['dns_over_tls'] = form_data['dns_over_tls']

        if old_data['dnssec'] != form_data['dnssec']:
            changes['dnssec'] = form_data['dnssec']

        if changes:
            privileged.set_resolved_configuration(**changes)
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)


class HostnameView(FormView):
    """View to update system's hostname."""
    template_name = 'form.html'
    form_class = HostnameForm
    prefix = 'hostname'
    success_url = reverse_lazy('names:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Set Hostname')
        return context

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['hostname'] = names.get_hostname()
        return initial

    def form_valid(self, form):
        """Apply the form changes."""
        if form.initial['hostname'] != form.cleaned_data['hostname']:
            try:
                names.set_hostname(form.cleaned_data['hostname'])
                messages.success(self.request, _('Configuration updated'))
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error setting hostname: {exception}').format(
                        exception=exception))

        return super().form_valid(form)


class DomainAddView(FormView):
    """View to update system's static domain name."""
    template_name = 'names-domain-add.html'
    form_class = DomainAddForm
    prefix = 'domain-add'
    success_url = reverse_lazy('names:index')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Domain Name')
        return context

    def form_valid(self, form):
        """Apply the form changes."""
        _domain_add(form.cleaned_data['domain_name'])
        messages.success(self.request, _('Configuration updated'))
        return super().form_valid(form)


class DomainDeleteView(TemplateView):
    """Confirm and delete a domain."""
    template_name = 'names-domain-delete.html'

    def get_context_data(self, **kwargs):
        """Return additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        domain = self.kwargs['domain']
        context['domain'] = domain
        context['title'] = str(
            _('Delete Domain {domain}?')).format(domain=domain)
        return context

    def post(self, request, domain):
        """Delete a domain."""
        _domain_delete(domain)
        messages.success(request, _('Domain deleted.'))
        return redirect('names:index')


def get_status() -> dict[str, object]:
    """Get configured services per name."""
    domains = components.DomainName.list()
    used_domain_types = {domain.domain_type for domain in domains}
    unused_domain_types = [
        domain_type for domain_type in components.DomainType.list().values()
        if domain_type not in used_domain_types or domain_type.add_url
    ]

    return {'domains': domains, 'unused_domain_types': unused_domain_types}


def _domain_add(domain_name: str):
    """Add a static domain name."""
    # Domain name is not case sensitive, but Let's Encrypt certificate
    # paths use lower-case domain name.
    domain_name = domain_name.lower()

    logger.info('Adding domain name - %s', domain_name)
    names.domain_add(domain_name)

    domain_added.send_robust(sender='names', domain_type='domain-type-static',
                             name=domain_name, services='__all__')


def _domain_delete(domain_name: str):
    """Remove a static domain name."""
    # Domain name is not case sensitive, but Let's Encrypt certificate
    # paths use lower-case domain name.
    domain_name = domain_name.lower()

    logger.info('Removing domain name - %s', domain_name)
    names.domain_delete(domain_name)

    # Update domain registered with Name Services module.
    domain_removed.send_robust(sender='names',
                               domain_type='domain-type-static',
                               name=domain_name)
