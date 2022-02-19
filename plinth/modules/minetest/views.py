# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for minetest module.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth.modules import names
from plinth.views import AppView

from . import get_configuration
from .forms import MinetestForm


class MinetestAppView(AppView):  # pylint: disable=too-many-ancestors
    """A specialized view for configuring minetest."""
    app_id = 'minetest'
    template_name = 'minetest.html'
    form_class = MinetestForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(get_configuration())
        return initial

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        context['domains'] = names.components.DomainName.list_names(
            'minetest-plinth')
        return context

    def form_valid(self, form):
        """Change the configurations of Minetest service."""
        data = form.cleaned_data
        old_config = get_configuration()
        updated = False

        if old_config['max_players'] != data['max_players'] \
           and data['max_players'] is not None:
            actions.superuser_run(
                'minetest',
                ['configure', '--max_players',
                 str(data['max_players'])])
            updated = True

        if old_config['creative_mode'] != data['creative_mode']:
            value = 'true' if data['creative_mode'] else 'false'
            actions.superuser_run('minetest',
                                  ['configure', '--creative_mode', value])
            updated = True

        if old_config['enable_pvp'] != data['enable_pvp']:
            value = 'true' if data['enable_pvp'] else 'false'
            actions.superuser_run('minetest',
                                  ['configure', '--enable_pvp', value])
            updated = True

        if old_config['enable_damage'] != data['enable_damage']:
            value = 'true' if data['enable_damage'] else 'false'
            actions.superuser_run('minetest',
                                  ['configure', '--enable_damage', value])
            updated = True

        if updated:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
