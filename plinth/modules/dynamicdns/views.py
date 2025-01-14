# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the dynamicsdns module."""

import datetime

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from plinth import views
from plinth.modules import dynamicdns

from .forms import DomainForm


class DynamicDNSAppView(views.AppView):
    """View to show app status."""

    app_id = 'dynamicdns'
    template_name = 'dynamicdns.html'

    _error_messages = {
        'timeout': _('Connection timed out'),
        'gaierror': _('Could not find server'),
        'TimeoutError': _('Connection timed out'),
        'ConnectionRefusedError': _('Server refused connection'),
        'ValueError': _('Already up-to-date')
    }

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        config = dynamicdns.get_config()
        context['domains'] = config['domains']

        status = dynamicdns.get_status()
        domains_status = {}
        for domain_name, domain in status['domains'].items():
            if domain_name not in config['domains']:
                continue

            # Create naive datetime object in local timezone
            domain['timestamp'] = datetime.datetime.fromtimestamp(
                domain['timestamp'])
            domains_status[domain_name] = domain
            if domain['error_code'] in self._error_messages:
                domain['error_message'] = self._error_messages[
                    domain['error_code']]

        context['domains_status'] = domains_status
        return context


class DomainView(FormView):
    """View to add/edit a dynamic DNS domain."""

    template_name = 'dynamicdns-domain.html'
    form_class = DomainForm
    prefix = 'domain'
    success_url = reverse_lazy('dynamicdns:index')

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        domain_name = self.kwargs.get('domain')
        if not domain_name:
            context['title'] = _('Add Dynamic Domain')
        else:
            context['title'] = _('Edit Dynamic Domain')

        return context

    def get_initial(self):
        """Get the current values for the form."""
        initial = super().get_initial()
        domain_name = self.kwargs.get('domain')
        domains = dynamicdns.get_config()['domains']
        domain = {}
        if domains and domain_name and domain_name in domains:
            domain = domains[domain_name]

        initial.update(domain)
        return domain

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status != new_status:
            try:
                _domain_delete(old_status['domain'])
            except KeyError:
                pass

            _domain_add(new_status['domain'], new_status)
            messages.success(self.request, _('Configuration updated'))

        # Perform an immediate update, even when configuration is not changed.
        dynamicdns.update_dns(None)

        return super().form_valid(form)


def _domain_add(domain: str, domain_config: dict):
    """Add a domain to the configuration."""
    config = dynamicdns.get_config()
    config['domains'][domain] = domain_config
    dynamicdns.set_config(config)
    dynamicdns.notify_domain_added(domain)


def _domain_delete(domain: str):
    """Remove a domain from the configuration.

    Raises KeyError if the domain is not found in the configuration.
    """
    config = dynamicdns.get_config()
    del config['domains'][domain]
    dynamicdns.set_config(config)
    if domain:
        dynamicdns.notify_domain_removed(domain)


class DomainDeleteView(TemplateView):
    """Confirm and delete a domain."""
    template_name = 'dynamicdns-domain-delete.html'

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
        try:
            _domain_delete(domain)
            messages.success(request, _('Domain deleted.'))
        except KeyError:
            raise

        return redirect('dynamicdns:index')
