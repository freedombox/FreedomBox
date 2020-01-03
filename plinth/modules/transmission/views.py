#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app for configuring Transmission Server.
"""

import json
import logging
import os
import socket

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import transmission

from .forms import TransmissionForm

logger = logging.getLogger(__name__)


class TransmissionAppView(views.AppView):
    """Serve configuration page."""
    clients = transmission.clients
    name = transmission.name
    description = transmission.description
    form_class = TransmissionForm
    app_id = 'transmission'
    manual_page = transmission.manual_page
    icon_filename = transmission.icon_filename

    def get_initial(self):
        """Get the current settings from Transmission server."""
        status = super().get_initial()
        configuration = actions.superuser_run('transmission',
                                              ['get-configuration'])
        configuration = json.loads(configuration)
        status['storage_path'] = os.path.normpath(
            configuration['download-dir'])
        status['hostname'] = socket.gethostname()

        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data

        if new_status['is_enabled'] or not old_status['is_enabled']:
            if old_status['storage_path'] != new_status['storage_path']:
                new_configuration = {
                    'download-dir': new_status['storage_path'],
                }

                actions.superuser_run(
                    'transmission', ['merge-configuration'],
                    input=json.dumps(new_configuration).encode())
                messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
