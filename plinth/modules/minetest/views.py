# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for minetest module."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.modules import names
from plinth.views import AppView

from . import get_configuration, privileged
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

        changes = {}
        if old_config['max_players'] != data['max_players'] \
           and data['max_players'] is not None:
            changes['max_players'] = data['max_players']

        if old_config['creative_mode'] != data['creative_mode']:
            changes['creative_mode'] = data['creative_mode']

        if old_config['enable_pvp'] != data['enable_pvp']:
            changes['enable_pvp'] = data['enable_pvp']

        if old_config['enable_damage'] != data['enable_damage']:
            changes['enable_damage'] = data['enable_damage']

        if changes:
            privileged.configure(**changes)
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
