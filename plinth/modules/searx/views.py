# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django views for Searx.
"""

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.errors import ActionError
from plinth.modules import searx

from .forms import SearxForm


class SearxAppView(views.AppView):
    """Serve configuration page."""
    app_id = 'searx'
    form_class = SearxForm
    show_status_block = False

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        initial['safe_search'] = searx.get_safe_search_setting()
        initial['public_access'] = searx.is_public_access_enabled() and \
            searx.app.is_enabled()
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_data = form.initial
        form_data = form.cleaned_data

        if str(old_data['safe_search']) != form_data['safe_search']:
            try:
                actions.superuser_run(
                    'searx', ['set-safe-search', form_data['safe_search']])
                messages.success(self.request, _('Configuration updated.'))
            except ActionError:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        if old_data['public_access'] != form_data['public_access']:
            try:
                if form_data['public_access']:
                    searx.enable_public_access()
                else:
                    searx.disable_public_access()
                messages.success(self.request, _('Configuration updated.'))
            except ActionError:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)
