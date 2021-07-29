# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring WordPress.
"""

import pathlib

from django.contrib import messages
from django.utils.translation import ugettext as _
from plinth import actions, views

from . import PUBLIC_ACCESS_FILE
from .forms import WordPressForm


class WordPressAppView(views.AppView):
    """Serve configuration page."""
    form_class = WordPressForm
    app_id = 'wordpress'

    def get_initial(self):
        """Get the current WordPress settings."""
        status = super().get_initial()
        status['is_public'] = pathlib.Path(PUBLIC_ACCESS_FILE).exists()
        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data
        if old_status['is_public'] != new_status['is_public']:
            actions.superuser_run(
                'wordpress',
                ['set-public', '--enable',
                 str(new_status['is_public'])])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
