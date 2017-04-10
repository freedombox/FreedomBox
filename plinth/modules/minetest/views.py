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
Views for minetest module.
"""

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.views import ServiceView


from . import description, managed_services, get_configuration
from .forms import MinetestForm


class MinetestServiceView(ServiceView): # pylint: disable=too-many-ancestors
    """A specialized view for configuring minetest."""
    service_id = managed_services[0]
    diagnostics_module_name = "minetest"
    description = description
    show_status_block = True
    form_class = MinetestForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(get_configuration())
        return initial

    def form_valid(self, form):
        """Change the configurations of Minetest service."""
        data = form.cleaned_data
        old_config = get_configuration()

        if old_config['max_players'] != data['max_players'] \
           and data['max_players'] != None:
            actions.superuser_run(
                'minetest',
                ['configure', '--max_players', str(data['max_players'])])
            messages.success(self.request,
                             _('Maximum players configuration updated'))

        if old_config['creative_mode'] != data['creative_mode']:
            value = 'true' if data['creative_mode'] else 'false'
            actions.superuser_run(
                'minetest',
                ['configure', '--creative_mode', value])
            messages.success(self.request,
                             _('Creative mode configuration updated'))

        if old_config['enable_pvp'] != data['enable_pvp']:
            value = 'true' if data['enable_pvp'] else 'false'
            actions.superuser_run(
                'minetest',
                ['configure', '--enable_pvp', value])
            messages.success(self.request,
                             _('PVP configuration updated'))

        if old_config['enable_damage'] != data['enable_damage']:
            value = 'true' if data['enable_damage'] else 'false'
            actions.superuser_run(
                'minetest',
                ['configure', '--enable_damage', value])
            messages.success(self.request,
                             _('Damage configuration updated'))

        return super().form_valid(form)
