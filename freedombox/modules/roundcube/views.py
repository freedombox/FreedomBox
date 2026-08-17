# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for roundcube.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.views import AppView

from . import privileged
from .forms import RoundcubeForm


class RoundcubeAppView(AppView):
    """Roundcube configuration page."""
    app_id = 'roundcube'
    form_class = RoundcubeForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial['local_only'] = privileged.get_config()['local_only']
        return initial

    def form_valid(self, form):
        """Change the config of Roundcube app."""
        old_data = form.initial
        data = form.cleaned_data
        if old_data['local_only'] != data['local_only']:
            privileged.set_config(data['local_only'])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
