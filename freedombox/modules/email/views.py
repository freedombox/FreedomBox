# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the email app.
"""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from freedombox.modules.email import dns
from freedombox.views import AppView

from . import aliases as aliases_module
from . import forms, privileged


class EmailAppView(AppView):
    """Server configuration page."""
    app_id = 'email'
    form_class = forms.DomainForm
    template_name = 'email.html'

    def get_context_data(self, **kwargs):
        """Add additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context.update(privileged.domain.get_domains())
        return context

    def get_initial(self):
        """Return the initial values to populate in the form."""
        initial = super().get_initial()
        domains = privileged.domain.get_domains()
        initial['primary_domain'] = domains['primary_domain']
        return initial

    def form_valid(self, form):
        """Update the settings for changed domain values."""
        old_data = form.initial
        new_data = form.cleaned_data
        if old_data['primary_domain'] != new_data['primary_domain']:
            try:
                privileged.domain.set_all_domains(new_data['primary_domain'])
                messages.success(self.request, _('Configuration updated'))
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)


class DnsView(TemplateView):
    """Show the DNS records to configure on a given domain."""
    template_name = 'email-dns.html'

    def get_context_data(self, **kwargs):
        """Add additional context data for rendering the template."""
        domain = self.kwargs['domain']
        context = super().get_context_data(**kwargs)
        primary_domain = privileged.domain.get_domains()['primary_domain']
        context['primary_domain'] = primary_domain
        context['dns_entries'] = dns.get_entries(domain)
        context['reverse_dns_entries'] = dns.get_reverse_entries(domain)
        return context


class AliasView(FormView):
    """View to list and delete aliases."""
    template_name = 'email-aliases.html'
    form_class = forms.AliasCreateForm
    success_url = reverse_lazy('email:aliases')

    def _get_current_aliases(self):
        """Return current list of all aliases."""
        return aliases_module.get()

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['aliases'] = self._get_current_aliases()
        return context

    def form_valid(self, form):
        """Handle a valid submission."""
        aliases_module.put(form.cleaned_data['username'],
                           form.cleaned_data['alias'])
        return HttpResponse(headers={'HX-Redirect': self.get_success_url()})


@require_POST
def alias_delete(request, alias):
    """View to delete an email alias."""
    aliases_module.delete([alias])
    return redirect(reverse_lazy('email:aliases'))


class XmlView(TemplateView):
    """Serve Thunderbird auto-configuration file.

    https://wiki.mozilla.org/Thunderbird:Autoconfiguration:ConfigFileFormat
    """
    template_name = 'email-autoconfig.xml'

    def render_to_response(self, *args, **kwargs):
        kwargs['content_type'] = 'text/xml; charset=utf-8'
        return super().render_to_response(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['host'] = self.request.get_host()
        return context
