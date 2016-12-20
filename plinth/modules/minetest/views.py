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

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.views import ServiceView

from . import description, managed_services, get_max_players_value, get_enable_pvp_value, get_creative_mode_value, get_enable_damage_value
from .forms import MinetestForm


class MinetestServiceView(ServiceView):
    """A specialized view for configuring minetest."""
    service_id = managed_services[0]
    diagnostics_module_name = "minetest"
    description = description
    show_status_block = True
    form_class = MinetestForm

def get_initial(self):
    """Return the values to fill in the form."""
    initial = super().get_initial()
    initial['max_players'] = get_max_players_value()
    initial['creative_mode'] = get_creative_mode_value()
    initial['enable_pvp'] = get_enable_pvp_value()
    initial['enable_damage'] = get_enable_damage_value()
    return initial
