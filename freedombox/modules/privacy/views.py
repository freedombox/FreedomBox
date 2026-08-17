# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for privacy app."""

from django.contrib import messages
from django.utils.translation import gettext as _

import plinth.modules.names.privileged as names_privileged
from plinth.modules import names, privacy
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
        initial['ip_lookup_url'] = privacy.get_ip_lookup_url()
        if names.is_resolved_installed():
            initial.update(names_privileged.get_resolved_configuration())

        return initial

    def form_valid(self, form):
        """Change the configurations of Minetest service."""
        new_config = form.cleaned_data
        old_config = form.initial

        changes = {}
        is_changed = False
        if old_config['enable_popcon'] != new_config['enable_popcon']:
            changes['enable_popcon'] = new_config['enable_popcon']

        if 'dns_fallback' in old_config:
            if old_config['dns_fallback'] != new_config['dns_fallback']:
                names_privileged.set_resolved_configuration(
                    dns_fallback=new_config['dns_fallback'])
                is_changed = True

        if old_config['ip_lookup_url'] != new_config['ip_lookup_url']:
            privacy.set_ip_lookup_url(new_config['ip_lookup_url'])
            is_changed = True

        if changes:
            privileged.set_configuration(**changes)

        if changes or is_changed:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
