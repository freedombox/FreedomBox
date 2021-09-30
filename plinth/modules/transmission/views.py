# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring Transmission Server.
"""

import json
import logging
import socket

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import actions, views

from .forms import TransmissionForm

logger = logging.getLogger(__name__)


class TransmissionAppView(views.AppView):
    """Serve configuration page."""
    form_class = TransmissionForm
    app_id = 'transmission'

    def get_initial(self):
        """Get the current settings from Transmission server."""
        status = super().get_initial()
        configuration = actions.superuser_run('transmission',
                                              ['get-configuration'])
        configuration = json.loads(configuration)
        status['storage_path'] = configuration['download-dir']
        status['hostname'] = socket.gethostname()

        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data
        if old_status['storage_path'] != new_status['storage_path']:
            new_configuration = {
                'download-dir': new_status['storage_path'],
            }

            actions.superuser_run('transmission', ['merge-configuration'],
                                  input=json.dumps(new_configuration).encode())
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
