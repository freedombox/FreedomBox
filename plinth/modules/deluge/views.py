# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django views for Deluge.
"""

import json
import os

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views

from .forms import DelugeForm


class DelugeAppView(views.AppView):
    """Serve configuration page."""
    diagnostics_module_name = 'deluge'
    form_class = DelugeForm
    app_id = 'deluge'

    def get_initial(self):
        """Get current Deluge server settings."""
        status = super().get_initial()
        configuration = json.loads(
            actions.superuser_run('deluge', ['get-configuration']))
        status['storage_path'] = os.path.normpath(
            configuration['download_location'])
        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data

        # don't change the configuration if the application was disabled
        if new_status['is_enabled'] or not old_status['is_enabled']:
            if old_status['storage_path'] != new_status['storage_path']:
                new_configuration = [
                    'download_location', new_status['storage_path']
                ]

                actions.superuser_run('deluge', ['set-configuration'] +
                                      new_configuration)
                messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
