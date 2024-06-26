# SPDX-License-Identifier: AGPL-3.0-or-later
"""Django views for Nextcloud app."""

import logging

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.modules.nextcloud.forms import NextcloudForm
from plinth.views import AppView

from . import privileged

logger = logging.getLogger(__name__)


class NextcloudAppView(AppView):
    """Show Nextcloud app main view."""

    app_id = 'nextcloud'
    form_class = NextcloudForm

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update({
            'override_domain': privileged.get_override_domain(),
            'default_phone_region': privileged.get_default_phone_region() or ''
        })
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        is_changed = False

        def _value_changed(key):
            return old_config.get(key) != new_config.get(key)

        if _value_changed('override_domain'):
            privileged.set_override_domain(new_config['override_domain'])
            is_changed = True

        if new_config['admin_password']:
            try:
                privileged.set_admin_password(new_config['admin_password'])
                is_changed = True
            except Exception:
                messages.error(
                    self.request,
                    _('Password update failed. Please choose a stronger '
                      'password.'))

        if _value_changed('default_phone_region'):
            privileged.set_default_phone_region(
                new_config['default_phone_region'])
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated.'))

        return super().form_valid(form)
