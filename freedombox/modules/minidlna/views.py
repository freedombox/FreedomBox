# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the minidlna module."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.views import AppView

from . import privileged
from .forms import MiniDLNAServerForm


class MiniDLNAAppView(AppView):
    """Show minidlna app view."""

    app_id = 'minidlna'
    form_class = MiniDLNAServerForm

    def get_initial(self):
        """Return initial values of the form."""
        initial = super().get_initial()
        initial.update({'storage_path': privileged.get_media_dir()})

        return initial

    def form_valid(self, form):
        """Apply changes from the form."""
        old_config = form.initial
        new_config = form.cleaned_data

        if old_config['storage_path'] != new_config['storage_path']:
            privileged.set_media_dir(new_config['storage_path'])
            messages.success(self.request, _('Updated media directory'))

        return super().form_valid(form)
