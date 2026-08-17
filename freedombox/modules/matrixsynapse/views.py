# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the Matrix Synapse module."""

import datetime

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView

from plinth import app as app_module
from plinth.forms import DomainSelectionForm
from plinth.modules import matrixsynapse, names
from plinth.modules.coturn.components import TurnConfiguration
from plinth.views import AppView

from . import get_turn_configuration, privileged
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

    def get_context_data(self, *args, **kwargs) -> dict[str, object]:
        """Provide context data to the template."""
        context = super().get_context_data(**kwargs)
        app = app_module.App.get('matrixsynapse')

        context['title'] = app.info.name
        context['app_info'] = app.info
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
        status = self.get_common_status()
        if status['is_enabled']:
            # App is disabled when uninstalling
            if not matrixsynapse.is_setup():
                return redirect('matrixsynapse:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['domain_name'] = matrixsynapse.get_configured_domain_name()
        context['certificate_status'] = matrixsynapse.get_certificate_status()
        context['config'] = privileged.get_config()
        tokens = privileged.list_registration_tokens()
        for token in tokens:
            if token['expiry_time']:
                date = datetime.datetime.utcfromtimestamp(
                    token['expiry_time'] / 1000)
                token['expiry_time'] = date

        context['registration_tokens'] = tokens
        return context

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        turn_config, managed = get_turn_configuration()
        config = privileged.get_config()
        initial.update({
            'enable_public_registration':
                config['public_registration'],
            'registration_verification':
                config['registration_verification'] or 'disabled',
            'enable_managed_turn':
                managed,
            'turn_uris':
                '\n'.join(turn_config.uris),
            'shared_secret':
                turn_config.shared_secret
        })
        return initial

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
        if (changed('enable_public_registration')
                or changed('registration_verification')):
            try:
                privileged.set_config(
                    public_registration=new_config[
                        'enable_public_registration'],
                    registration_verification=new_config[
                        'registration_verification'])
                is_changed = True
            except ProcessLookupError:
                # Matrix Synapse server is not running
                messages.error(
                    self.request,
                    _('Registration configuration cannot be updated when app '
                      'is disabled.'))

        if changed('enable_managed_turn') or changed('turn_uris') or \
           changed('shared_secret'):
            self._handle_turn_configuration(old_config, new_config)
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
