# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Home Assistant app."""

import logging

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.forms import DomainSelectionForm
from plinth.views import AppView

logger = logging.getLogger(__name__)


class HomeAssistantAppView(AppView):
    """Show Home Assistant app main view."""

    app_id = 'homeassistant'
    template_name = 'homeassistant.html'
    form_class = DomainSelectionForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        component = self.app.get_component('webserverroot-homeassistant')
        initial.update({
            'domain_name': component.domain_get() or '',
        })
        return initial

    def get_form_kwargs(self):
        """Return the arguments to instantiate form with."""
        kwargs = super().get_form_kwargs()
        kwargs['show_none'] = True
        return kwargs

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        is_changed = False

        def _value_changed(key):
            return old_config.get(key) != new_config.get(key)

        if _value_changed('domain_name'):
            component = self.app.get_component('webserverroot-homeassistant')
            component.domain_set(new_config['domain_name'] or None)
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated.'))

        return super().form_valid(form)
