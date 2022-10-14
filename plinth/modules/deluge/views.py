# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Deluge."""

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import views

from . import privileged
from .forms import DelugeForm


class DelugeAppView(views.AppView):
    """Serve configuration page."""

    diagnostics_module_name = 'deluge'
    form_class = DelugeForm
    app_id = 'deluge'

    def get_initial(self):
        """Get current Deluge server settings."""
        status = super().get_initial()
        configuration = privileged.get_configuration()
        status['storage_path'] = configuration['download_location']
        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['storage_path'] != new_status['storage_path']:
            privileged.set_configuration(
                download_location=new_status['storage_path'])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
