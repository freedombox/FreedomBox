# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Matrix Synapse module.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from plinth import actions
from plinth.forms import DomainSelectionForm
from plinth.modules import matrixsynapse, names
from plinth.modules.coturn.components import TurnConfiguration
from plinth.views import AppView

from . import get_public_registration_status, get_turn_configuration
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
        config, managed = get_turn_configuration()
        initial.update({
            'enable_public_registration': get_public_registration_status(),
            'enable_managed_turn': managed,
            'turn_uris': '\n'.join(config.uris),
            'shared_secret': config.shared_secret
        })
        return initial

    @staticmethod
    def _handle_public_registrations(new_config):
        if new_config['enable_public_registration']:
            actions.superuser_run('matrixsynapse',
                                  ['public-registration', 'enable'])
        else:
            actions.superuser_run('matrixsynapse',
                                  ['public-registration', 'disable'])

    @staticmethod
    def _handle_turn_configuration(old_config, new_config):
        if not new_config['enable_managed_turn']:
            new_turn_uris = new_config['turn_uris'].splitlines()
            new_shared_secret = new_config['shared_secret']

            turn_config_changed = \
                old_config['turn_uris'] != new_turn_uris or \
                old_config['shared_secret'] != new_shared_secret

            if turn_config_changed:
                matrixsynapse.update_turn_configuration(
                    TurnConfiguration(None, new_turn_uris, new_shared_secret),
                    managed=False)
        else:
            # Remove overridden turn configuration
            matrixsynapse.update_turn_configuration(TurnConfiguration(),
                                                    managed=False)

    def form_valid(self, form):
        """Handle valid form submission."""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        def changed(prop):
            return old_config[prop] != new_config[prop]

        is_changed = False
        if changed('enable_public_registration'):
            self._handle_public_registrations(new_config)
            is_changed = True

        if changed('enable_managed_turn') or changed('turn_uris') or \
           changed('shared_secret'):
            self._handle_turn_configuration(old_config, new_config)
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
