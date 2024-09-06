# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for name services.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.views import AppView

from . import components, privileged, resolved
from .forms import NamesConfigurationForm


class NamesAppView(AppView):
    """Show names app main page."""

    app_id = 'names'
    template_name = 'names.html'
    prefix = 'names'
    form_class = NamesConfigurationForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(privileged.get_resolved_configuration())
        return initial

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['status'] = get_status()
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


def get_status():
    """Get configured services per name."""
    domains = components.DomainName.list()
    used_domain_types = {domain.domain_type for domain in domains}
    unused_domain_types = [
        domain_type for domain_type in components.DomainType.list().values()
        if domain_type not in used_domain_types
    ]

    return {'domains': domains, 'unused_domain_types': unused_domain_types}
