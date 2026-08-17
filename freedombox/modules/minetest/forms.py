# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Forms for minetest module.
"""

from django import forms
from django.utils.translation import gettext_lazy as _


class MinetestForm(forms.Form):
    """Minetest configuration form"""
    max_players = forms.IntegerField(
        label=_('Maximum number of players'), required=True, min_value=1,
        max_value=100,
        help_text=_('You can change the maximum number of players playing '
                    'minetest at a single instance of time.'))

    creative_mode = forms.BooleanField(
        label=_('Enable creative mode'), required=False,
        help_text=_('Creative mode changes the rules of the game to make it '
                    'more suitable for creative gameplay, rather than '
                    'challenging "survival" gameplay.'))

    enable_pvp = forms.BooleanField(
        label=_('Enable PVP'), required=False,
        help_text=_('Enabling Player Vs Player will allow players to damage '
                    'other players.'))

    enable_damage = forms.BooleanField(
        label=_('Enable damage'), required=False,
        help_text=_('When disabled, players cannot die or receive damage of '
                    'any kind.'))
