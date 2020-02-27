# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring date and time.
"""

import logging

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions
from plinth.views import AppView

from .forms import DateTimeForm

logger = logging.getLogger(__name__)


class DateTimeAppView(AppView):
    form_class = DateTimeForm
    app_id = 'datetime'

    def get_initial(self):
        status = super().get_initial()
        status['time_zone'] = self.get_current_time_zone()
        return status

    def get_current_time_zone(self):
        """Get current time zone."""
        time_zone = open('/etc/timezone').read().rstrip()
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
