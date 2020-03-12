# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Plinth views for Coquelicot.
"""

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.errors import ActionError
from plinth.modules.coquelicot import get_current_max_file_size

from .forms import CoquelicotForm


class CoquelicotAppView(views.AppView):
    """Serve configuration page."""
    app_id = 'coquelicot'
    form_class = CoquelicotForm

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        initial['max_file_size'] = get_current_max_file_size()
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        form_data = form.cleaned_data

        if form_data['upload_password']:
            try:
                actions.superuser_run(
                    'coquelicot', ['set-upload-password'],
                    input=form_data['upload_password'].encode())
                messages.success(self.request, _('Upload password updated'))
            except ActionError:
                messages.error(self.request,
                               _('Failed to update upload password'))

        max_file_size = form_data['max_file_size']
        if max_file_size and max_file_size != get_current_max_file_size():
            try:
                actions.superuser_run(
                    'coquelicot', ['set-max-file-size',
                                   str(max_file_size)])
                messages.success(self.request, _('Maximum file size updated'))
            except ActionError:
                messages.error(self.request,
                               _('Failed to update maximum file size'))

        return super().form_valid(form)
