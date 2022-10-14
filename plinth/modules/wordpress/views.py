# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring WordPress."""

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import views

from . import privileged
from .forms import WordPressForm


class WordPressAppView(views.AppView):
    """Serve configuration page."""

    form_class = WordPressForm
    app_id = 'wordpress'

    def get_initial(self):
        """Get the current WordPress settings."""
        status = super().get_initial()
        status['is_public'] = privileged.is_public()
        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data
        if old_status['is_public'] != new_status['is_public']:
            privileged.set_public(new_status['is_public'])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
