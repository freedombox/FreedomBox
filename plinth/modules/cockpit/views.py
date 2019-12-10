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
Views for the Cockpit module
"""
from plinth.views import AppView
from plinth.modules.cockpit import (
    name,
    description,
    clients,
    manual_page,
    icon_filename,
)
from plinth.modules.cockpit.utils import get_origin_domains, load_augeas


class CockpitAppView(AppView):
    app_id = 'cockpit'
    name = name
    description = description
    diagnostics_module_name = 'cockpit'
    show_status_block = True
    clients = clients
    manual_page = manual_page
    template_name = 'cockpit.html'
    icon_filename = icon_filename

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['urls'] = get_origin_domains(load_augeas())

        return context
