# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for mumble app.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.modules import mumble
from plinth.modules.mumble.forms import MumbleForm
from plinth.views import AppView

from . import privileged


class MumbleAppView(AppView):
    app_id = 'mumble'
    form_class = MumbleForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = mumble.get_domain()
        initial['root_channel_name'] = privileged.get_root_channel_name()
        return initial

    def form_valid(self, form):
        """Apply form changes."""
        new_config = form.cleaned_data

        if mumble.get_domain() != new_config['domain']:
            privileged.set_domain(new_config['domain'])
            mumble.app.get_component('letsencrypt-mumble').setup_certificates()
            messages.success(self.request, _('Configuration updated'))

        password = new_config.get('super_user_password')
        if password:
            privileged.set_super_user_password(password)
            messages.success(self.request,
                             _('SuperUser password successfully updated.'))

        join_password = new_config.get('join_password')
        if join_password:
            privileged.change_join_password(join_password)
            messages.success(self.request, _('Join password changed'))

        name = new_config.get('root_channel_name')
        if name:
            privileged.change_root_channel_name(name)
            messages.success(self.request, _('Root channel name changed.'))

        return super().form_valid(form)
