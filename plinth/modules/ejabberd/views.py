# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the Ejabberd app."""

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth.modules import coturn, ejabberd
from plinth.modules.coturn.components import TurnConfiguration
from plinth.views import AppView

from . import privileged
from .forms import EjabberdForm


class EjabberdAppView(AppView):
    """Show ejabberd as a service."""

    app_id = 'ejabberd'
    template_name = 'ejabberd.html'
    form_class = EjabberdForm

    def get_initial(self):
        """Return initial data to fill in the form."""
        config, managed = ejabberd.get_turn_configuration()
        return super().get_initial() | {
            'domain_names': ejabberd.get_domains(),
            'MAM_enabled': privileged.mam('status'),
            'enable_managed_turn': managed,
            'turn_uris': '\n'.join(config.uris),
            'shared_secret': config.shared_secret
        }

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        domains = ejabberd.get_domains()
        context['domainname'] = domains[0] if domains else None
        return context

    @staticmethod
    def _handle_domain_names_configuration(new_config):
        """Update list of domain names in configuration."""
        ejabberd.set_domains(new_config['domain_names'])

    @staticmethod
    def _handle_turn_configuration(old_config, new_config):
        if not new_config['enable_managed_turn']:
            new_turn_uris = new_config['turn_uris'].splitlines()
            new_shared_secret = new_config['shared_secret']

            turn_config_changed = \
                old_config['turn_uris'] != new_turn_uris or \
                old_config['shared_secret'] != new_shared_secret

            if turn_config_changed:
                ejabberd.update_turn_configuration(
                    TurnConfiguration(None, new_turn_uris, new_shared_secret),
                    managed=False)
        else:
            ejabberd.update_turn_configuration(coturn.get_config(),
                                               managed=True)

    @staticmethod
    def _handle_MAM_configuration(old_config, new_config):
        # note ejabberd action "enable" or "disable" restarts, if running
        if new_config['MAM_enabled']:
            privileged.mam('enable')
        else:
            privileged.mam('disable')

    def form_valid(self, form):
        """Enable/disable a service and set messages."""
        old_config = form.initial
        new_config = form.cleaned_data

        def changed(prop):
            return old_config[prop] != new_config[prop]

        is_changed = False

        if changed('domain_names'):
            self._handle_domain_names_configuration(new_config)
            is_changed = True

        if changed('MAM_enabled'):
            self._handle_MAM_configuration(old_config, new_config)
            is_changed = True

        if changed('enable_managed_turn') or changed('turn_uris') or \
           changed('shared_secret'):
            self._handle_turn_configuration(old_config, new_config)
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
