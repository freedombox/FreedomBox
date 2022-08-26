# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Searx."""

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import app as app_module
from plinth import views
from plinth.modules import searx

from . import privileged
from .forms import SearxForm


class SearxAppView(views.AppView):
    """Serve configuration page."""

    app_id = 'searx'
    form_class = SearxForm

    def get_initial(self):
        """Return the status of the service to fill in the form."""
        initial = super().get_initial()
        initial['safe_search'] = privileged.get_safe_search()
        initial['public_access'] = searx.is_public_access_enabled() and \
            app_module.App.get('searx').is_enabled()
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_data = form.initial
        form_data = form.cleaned_data

        if str(old_data['safe_search']) != form_data['safe_search']:
            try:
                privileged.set_safe_search(int(form_data['safe_search']))
                messages.success(self.request, _('Configuration updated.'))
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        if old_data['public_access'] != form_data['public_access']:
            try:
                if form_data['public_access']:
                    searx.enable_public_access()
                else:
                    searx.disable_public_access()
                messages.success(self.request, _('Configuration updated.'))
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)
