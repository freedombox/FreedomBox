# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring date and time.
"""

import logging
import pathlib

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import actions
from plinth.views import AppView

from .forms import DateTimeForm

logger = logging.getLogger(__name__)


class DateTimeAppView(AppView):
    """Serve configuration page."""
    form_class = DateTimeForm
    app_id = 'datetime'

    def get_initial(self):
        status = super().get_initial()
        status['time_zone'] = self.get_current_time_zone()
        return status

    @staticmethod
    def get_current_time_zone():
        """Get current time zone."""
        path = pathlib.Path('/etc/timezone')
        time_zone = path.read_text(encoding='utf-8').rstrip()
        return time_zone or 'none'

    def form_valid(self, form):
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['time_zone'] != new_status['time_zone'] and \
           new_status['time_zone'] != 'none':
            try:
                actions.superuser_run('timezone-change',
                                      [new_status['time_zone']])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error setting time zone: {exception}').format(
                        exception=exception))
            else:
                messages.success(self.request, _('Time zone set'))

        return super().form_valid(form)
