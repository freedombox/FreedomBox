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
Django views for Deluge.
"""

import json
import os

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import deluge

from .forms import DelugeForm


class DelugeAppView(views.AppView):
    """Serve configuration page."""
    clients = deluge.clients
    name = deluge.name
    description = deluge.description
    diagnostics_module_name = 'deluge'
    form_class = DelugeForm
    app_id = 'deluge'
    manual_page = deluge.manual_page
    icon_filename = deluge.icon_filename

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

                actions.superuser_run(
                    'deluge', ['set-configuration'] + new_configuration)
                messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
