# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for radicale module.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.views import AppView

from . import get_rights_value, privileged
from .forms import RadicaleForm


class RadicaleAppView(AppView):
    """A specialized view for configuring radicale service."""
    form_class = RadicaleForm
    app_id = 'radicale'

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['access_rights'] = get_rights_value()
        return initial

    def form_valid(self, form):
        """Change the access control of Radicale service."""
        data = form.cleaned_data
        if get_rights_value() != data['access_rights']:
            privileged.configure(data['access_rights'])
            messages.success(self.request,
                             _('Access rights configuration updated'))
        return super().form_valid(form)
