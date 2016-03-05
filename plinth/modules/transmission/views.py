#
# This file is part of Plinth.
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
Plinth module for configuring Transmission Server
"""

from django.contrib import messages
from django.utils.translation import ugettext as _
import json
import logging

from .forms import TransmissionForm
from plinth import actions
from plinth import views

logger = logging.getLogger(__name__)


class ConfigurationView(views.ConfigurationView):
    """Serve configuration page."""
    form_class = TransmissionForm

    def apply_changes(self, old_status, new_status):
        """Apply the changes submitted in the form."""
        modified = super().apply_changes(old_status, new_status)

        if old_status['download_dir'] != new_status['download_dir'] or \
           old_status['rpc_username'] != new_status['rpc_username'] or \
           old_status['rpc_password'] != new_status['rpc_password']:
            new_configuration = {
                'download-dir': new_status['download_dir'],
                'rpc-username': new_status['rpc_username'],
                'rpc-password': new_status['rpc_password'],
            }

            actions.superuser_run('transmission', ['merge-configuration'],
                                  input=json.dumps(new_configuration).encode())
            messages.success(self.request, _('Configuration updated'))
            return True

        return modified
