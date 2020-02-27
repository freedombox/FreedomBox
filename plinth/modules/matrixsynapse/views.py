# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Matrix Synapse module.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import FormView

from plinth import actions
from plinth.forms import DomainSelectionForm
from plinth.modules import matrixsynapse, names
from plinth.views import AppView

from . import get_public_registration_status
from .forms import MatrixSynapseForm


class SetupView(FormView):
    """Show matrix-synapse setup page."""
    template_name = 'matrix-synapse-pre-setup.html'
    form_class = DomainSelectionForm
    success_url = reverse_lazy('matrixsynapse:index')

    def form_valid(self, form):
        """Handle valid form submission."""
        matrixsynapse.setup_domain(form.cleaned_data['domain_name'])
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        """Provide context data to the template."""
        context = super().get_context_data(**kwargs)

        context['title'] = matrixsynapse.app.info.name
        context['app_info'] = matrixsynapse.app.info
        context['domain_names'] = names.components.DomainName.list_names(
            'matrix-synapse-plinth')

        return context


class MatrixSynapseAppView(AppView):
    """Show matrix-synapse service page."""
    app_id = 'matrixsynapse'
    template_name = 'matrix-synapse.html'
    form_class = MatrixSynapseForm
    port_forwarding_info = matrixsynapse.port_forwarding_info

    def dispatch(self, request, *args, **kwargs):
        """Redirect to setup page if setup is not done yet."""
        if not matrixsynapse.is_setup():
            return redirect('matrixsynapse:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['domain_name'] = matrixsynapse.get_configured_domain_name()
        context['certificate_status'] = matrixsynapse.get_certificate_status()
        return context

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update({
            'enable_public_registration': get_public_registration_status(),
        })
        return initial

    def form_valid(self, form):
        """Handle valid form submission."""
        old_config = self.get_initial()
        new_config = form.cleaned_data
        app_same = old_config['is_enabled'] == new_config['is_enabled']
        pubreg_same = old_config['enable_public_registration'] == \
            new_config['enable_public_registration']

        if app_same and pubreg_same:
            # TODO: find a more reliable/official way to check whether the
            # request has messages attached.
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_config['is_enabled']:
                self.app.enable()
            else:
                self.app.disable()

        if not pubreg_same:
            # note action public-registration restarts, if running now
            if new_config['enable_public_registration']:
                actions.superuser_run('matrixsynapse',
                                      ['public-registration', 'enable'])
                messages.success(self.request,
                                 _('Public registration enabled'))
            else:
                actions.superuser_run('matrixsynapse',
                                      ['public-registration', 'disable'])
                messages.success(self.request,
                                 _('Public registration disabled'))

        return super().form_valid(form)
