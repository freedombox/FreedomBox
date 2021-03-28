# SPDX-License-Identifier: AGPL-3.0-or-later
import plinth
from . import forms


class EmailServerView(plinth.views.AppView):
    """Server configuration page"""
    app_id = 'email_server'
    form_class = forms.EmailServerForm

    def form_valid(self, form):
        # old_settings = form.initial
        # new_status = form.cleaned_data
        # plinth.actions.superuser_run('email_server', ['--help'])
        return super().form_valid(form)
