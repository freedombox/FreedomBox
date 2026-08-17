# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring Transmission Server.
"""

import logging
import socket

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import views

from . import get_download_dir, privileged
from .forms import TransmissionForm

logger = logging.getLogger(__name__)


class TransmissionAppView(views.AppView):
    """Serve configuration page."""
    form_class = TransmissionForm
    app_id = 'transmission'

    def get_initial(self):
        """Get the current settings from Transmission server."""
        status = super().get_initial()
        status['storage_path'] = get_download_dir()
        status['hostname'] = socket.gethostname()

        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data
        if old_status['storage_path'] != new_status['storage_path']:
            new_configuration = {
                'download-dir': new_status['storage_path'],
                'download_dir': new_status['storage_path'],
            }
            privileged.merge_configuration(new_configuration)
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
