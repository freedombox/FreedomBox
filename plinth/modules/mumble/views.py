# SPDX-License-Identifier: AGPL-3.0-or-later
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth.modules import mumble
from plinth.modules.mumble.forms import MumbleForm
from plinth.views import AppView


class MumbleAppView(AppView):
    app_id = 'mumble'
    form_class = MumbleForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['domain'] = mumble.get_domain()
        return initial

    def form_valid(self, form):
        """Apply new superuser password if it exists"""
        new_config = form.cleaned_data

        if mumble.get_domain() != new_config['domain']:
            mumble.set_domain(new_config['domain'])
            mumble.app.get_component('letsencrypt-mumble').setup_certificates()
            messages.success(self.request, _('Configuration updated'))

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
