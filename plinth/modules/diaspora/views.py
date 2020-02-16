# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the diaspora module
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from plinth.forms import DomainSelectionForm
from plinth.modules import diaspora, names
from plinth.views import AppView

from .forms import DiasporaAppForm


class DiasporaSetupView(FormView):
    """Show diaspora setup page."""
    template_name = 'diaspora-pre-setup.html'
    form_class = DomainSelectionForm
    description = diaspora.app.info.description
    title = diaspora.app.info.name
    success_url = reverse_lazy('diaspora:index')

    def form_valid(self, form):
        domain_name = form.cleaned_data['domain_name']
        diaspora.setup_domain_name(domain_name)

        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = self.description
        context['title'] = self.title
        context['domain_names'] = names.components.DomainName.list_names(
            'https')

        return context


class DiasporaAppView(AppView):
    """Show diaspora service page."""
    form_class = DiasporaAppForm
    app_id = 'diaspora'
    template_name = 'diaspora-post-setup.html'

    def dispatch(self, request, *args, **kwargs):
        if not diaspora.is_setup():
            return redirect('diaspora:setup')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain_name'] = diaspora.get_configured_domain_name()
        return context

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        status = super().get_initial()
        status['is_user_registrations_enabled'] = \
            diaspora.is_user_registrations_enabled()
        return status

    def form_valid(self, form):
        """Enable/disable user registrations"""
        old_enabled = form.initial['is_enabled']
        new_enabled = form.cleaned_data['is_enabled']
        old_registration = form.initial['is_user_registrations_enabled']
        new_registration = form.cleaned_data['is_user_registrations_enabled']

        if old_registration == new_registration:
            if old_enabled == new_enabled:
                if not self.request._messages._queued_messages:
                    messages.info(self.request, _('Setting unchanged'))
        else:
            if new_registration:
                diaspora.enable_user_registrations()
                messages.success(self.request, _('User registrations enabled'))
            else:
                diaspora.disable_user_registrations()
                messages.success(self.request,
                                 _('User registrations disabled'))

        return super().form_valid(form)
