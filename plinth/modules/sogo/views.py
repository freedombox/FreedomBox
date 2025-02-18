# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the SOGo app."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.privileged import service as service_privileged
from plinth.views import AppView

from . import forms, privileged


class SOGoAppView(AppView):
    """Server configuration page."""
    app_id = 'sogo'
    form_class = forms.DomainForm

    def get_initial(self):
        """Return the initial values to populate in the form."""
        initial = super().get_initial()
        initial['domain'] = privileged.get_domain()
        return initial

    def form_valid(self, form):
        """Update the settings for changed domain values."""
        old_data = form.initial
        new_data = form.cleaned_data
        if old_data['domain'] != new_data['domain']:
            privileged.set_domain(new_data['domain'])
            service_privileged.try_restart('sogo')
            service_privileged.try_restart('memcached')
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
