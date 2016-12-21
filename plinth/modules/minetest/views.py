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
from plinth import action_utils


from . import description, managed_services, get_max_players_value,\
              get_enable_pvp_value, get_creative_mode_value,\
              get_enable_damage_value
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

        value=get_max_players_value();
        value = int(value)
        initial['max_players'] = value
        initial['creative_mode'] = get_creative_mode_value()
        initial['enable_pvp'] = get_enable_pvp_value()
        initial['enable_damage'] = get_enable_damage_value()
        return initial

    def form_valid(self, form):
        """Change the configurations of Minetest service."""
        data = form.cleaned_data
        char_value = str(data['max_players'])

        if get_max_players_value() != char_value:
            actions.superuser_run(
                'minetest',
                ['configure', '--max_players', char_value])
            messages.success(self.request,
                             _('Maximum players configuration updated')+char_value)

        if data['creative_mode'] is True:
            value = "true"
        else:
            value = "false"

        if get_creative_mode_value() != data['creative_mode']:
            actions.superuser_run(
                'minetest',
                ['configure', '--creative_mode', value])
            messages.success(self.request,
                             _('Creative mode configuration updated')+char_value)

        if data['enable_pvp'] is True:
            value = "true"
        else:
            value = "false"

        if get_enable_pvp_value() != data['enable_pvp']:
            actions.superuser_run(
                'minetest',
                ['configure', '--enable_pvp', value])
            messages.success(self.request,
                             _('PvP configuration updated'))

        if data['enable_damage'] is True:
            value = "true"
        else:
            value = "false"

        if get_enable_damage_value() != data['enable_damage']:
            actions.superuser_run(
                'minetest',
                ['configure', '--enable_damage', value])
            messages.success(self.request,
                             _('Damage configuration updated'))


        return super().form_valid(form)
