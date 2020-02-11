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
Plinth views for Coquelicot.
"""

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.errors import ActionError
from plinth.modules.coquelicot import get_current_max_file_size

from .forms import CoquelicotForm


class CoquelicotAppView(views.AppView):
    """Serve configuration page."""
    app_id = 'coquelicot'
    form_class = CoquelicotForm
    show_status_block = True

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        initial['max_file_size'] = get_current_max_file_size()
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        form_data = form.cleaned_data

        if form_data['upload_password']:
            try:
                actions.superuser_run(
                    'coquelicot', ['set-upload-password'],
                    input=form_data['upload_password'].encode())
                messages.success(self.request, _('Upload password updated'))
            except ActionError:
                messages.error(self.request,
                               _('Failed to update upload password'))

        max_file_size = form_data['max_file_size']
        if max_file_size and max_file_size != get_current_max_file_size():
            try:
                actions.superuser_run(
                    'coquelicot', ['set-max-file-size',
                                   str(max_file_size)])
                messages.success(self.request, _('Maximum file size updated'))
            except ActionError:
                messages.error(self.request,
                               _('Failed to update maximum file size'))

        return super().form_valid(form)
