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
Forms for minetest module.
"""

from django import forms
from django.utils.translation import ugettext_lazy as _

from plinth.forms import ServiceForm


class MinetestForm(ServiceForm):
    """Minetest configuration form"""
    max_players = forms.IntegerField(
        label=_('Maximum number of players'),
        required=True,
        min_value=1,
        max_value=100,
        help_text=_('You can change the maximum number of players playing \
                     minetest at a single instance of time'))

    creative_mode = forms.BooleanField(
        label=_('Enable creative mode'),
        required=False,
        help_text=_('Creative mode changes the rules of the game to make it \
                     more suitable for creative gameplay, rather than \
                     challenging "survival" gameplay.'))

    enable_pvp = forms.BooleanField(
        label=_('Enable PVP'),
        required=False,
        help_text=_('Enabling Player Vs Player will allow players to damage \
                    other players'))

    enable_damage = forms.BooleanField(
        label=_('Enable damage'),
        required=False,
        help_text=_('When disabled, players cannot die or receive damage of \
                    any kind'))
