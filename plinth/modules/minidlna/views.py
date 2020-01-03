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
Views for the minidlna module
"""
import os

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.modules import minidlna
from plinth.views import AppView

from .forms import MiniDLNAServerForm


class MiniDLNAAppView(AppView):
    app_id = 'minidlna'
    name = minidlna.name
    description = minidlna.description
    form_class = MiniDLNAServerForm
    icon_filename = minidlna.icon_filename
    clients = minidlna.clients

    def get_initial(self):
        """Initial form value as found in the minidlna.conf"""
        initial = super().get_initial()
        initial.update({
            'media_dir': actions.superuser_run('minidlna', ['get-media-dir']),
        })

        return initial

    def form_valid(self, form):
        """Apply changes from the form"""
        old_config = form.initial
        new_config = form.cleaned_data

        if old_config['media_dir'].strip() != new_config['media_dir']:
            if os.path.isdir(new_config['media_dir']) is False:
                messages.error(self.request,
                               _('Specified directory does not exist.'))
            else:
                actions.superuser_run(
                    'minidlna',
                    ['set-media-dir', '--dir', new_config['media_dir']])
                messages.success(self.request, _('Updated media directory'))

        return super().form_valid(form)
