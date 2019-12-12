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
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.modules.mumble import (clients, description, icon_filename,
                                   manual_page, name, port_forwarding_info)
from plinth.modules.mumble.forms import MumbleForm
from plinth.views import AppView


class MumbleAppView(AppView):
    app_id = 'mumble'
    diagnostics_module_name = 'mumble'
    name = name
    description = description
    clients = clients
    manual_page = manual_page
    port_forwarding_info = port_forwarding_info
    icon_filename = icon_filename
    form_class = MumbleForm

    def form_valid(self, form):
        """Apply new superuser password if it exists"""
        new_config = form.cleaned_data

        password = new_config.get('super_user_password')
        if password:
            actions.run_as_user(
                'mumble',
                ['create-password'],
                input=password.encode(),
                become_user="mumble-server",
            )
            messages.success(self.request,
                             _('SuperUser password successfully updated.'))

        return super().form_valid(form)
