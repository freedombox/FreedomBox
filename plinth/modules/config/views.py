# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox views for basic system configuration."""

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import views
from plinth.modules import config

from . import privileged
from .forms import ConfigurationForm


class ConfigAppView(views.AppView):
    """Serve configuration page."""

    form_class = ConfigurationForm
    app_id = 'config'

    def get_initial(self):
        """Return the current status."""
        return {
            'homepage': config.get_home_page(),
            'advanced_mode': config.get_advanced_mode(),
            'logging_mode': privileged.get_logging_mode(),
        }

    def form_valid(self, form):
        """Apply the form changes."""
        old_status = form.initial
        new_status = form.cleaned_data

        is_changed = False

        if old_status['homepage'] != new_status['homepage']:
            try:
                config.change_home_page(new_status['homepage'])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error setting webserver home page: {exception}').format(
                        exception=exception))
            else:
                messages.success(self.request, _('Webserver home page set'))

        if old_status['advanced_mode'] != new_status['advanced_mode']:
            try:
                config.set_advanced_mode(new_status['advanced_mode'])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error changing advanced mode: {exception}').format(
                        exception=exception))
            else:
                if new_status['advanced_mode']:
                    messages.success(self.request,
                                     _('Showing advanced apps and features'))
                else:
                    messages.success(self.request,
                                     _('Hiding advanced apps and features'))

        if old_status['logging_mode'] != new_status['logging_mode']:
            privileged.set_logging_mode(new_status['logging_mode'])
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
