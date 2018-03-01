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
import socket

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import transmission

from .forms import TransmissionForm

logger = logging.getLogger(__name__)


class TransmissionServiceView(views.ServiceView):
    """Serve configuration page."""
    clients = transmission.clients
    description = transmission.description
    diagnostics_module_name = 'transmission'
    form_class = TransmissionForm
    service_id = transmission.managed_services[0]
    manual_page = transmission.manual_page

    def get_initial(self):
        """Get the current settings from Transmission server."""
        configuration = actions.superuser_run('transmission',
                                              ['get-configuration'])
        status = json.loads(configuration)
        status = {
            key.translate(str.maketrans({
                '-': '_'
            })): value
            for key, value in status.items()
        }
        status['is_enabled'] = self.service.is_enabled()
        status['is_running'] = self.service.is_running()
        status['hostname'] = socket.gethostname()

        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['download_dir'] != new_status['download_dir']:
            new_configuration = {
                'download-dir': new_status['download_dir'],
            }

            actions.superuser_run('transmission', ['merge-configuration'],
                                  input=json.dumps(new_configuration).encode())
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
