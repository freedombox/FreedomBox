# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for privacy app."""

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth.modules.privacy.forms import PrivacyForm
from plinth.views import AppView

from . import privileged


class PrivacyAppView(AppView):
    """Serve configuration page."""

    app_id = 'privacy'
    form_class = PrivacyForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(privileged.get_configuration())
        return initial

    def form_valid(self, form):
        """Change the configurations of Minetest service."""
        new_config = form.cleaned_data
        old_config = form.initial

        changes = {}
        if old_config['enable_popcon'] != new_config['enable_popcon']:
            changes['enable_popcon'] = new_config['enable_popcon']

        if changes:
            privileged.set_configuration(**changes)
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
