# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Tiny Tiny RSS app."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.forms import TLSDomainForm
from plinth.views import AppView

from . import privileged


class TTRSSAppView(AppView):
    """Show TTRSS app main view."""

    app_id = 'ttrss'
    form_class = TLSDomainForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = privileged.get_domain()
        return initial

    def form_valid(self, form):
        """Change the domain of TT-RSS app."""
        data = form.cleaned_data
        old_data = form.initial
        if old_data['domain'] != data['domain']:
            privileged.set_domain(data['domain'])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
