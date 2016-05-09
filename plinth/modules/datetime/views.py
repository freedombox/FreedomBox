#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for configuring date and time
"""

from django.contrib import messages
from django.utils.translation import ugettext as _
import logging

from .forms import DateTimeForm
from plinth import actions
from plinth.modules import datetime
from plinth.views import ServiceView

logger = logging.getLogger(__name__)


class DateTimeServiceView(ServiceView):
    description = datetime.description
    form_class = DateTimeForm
    service_id = datetime.managed_services[0]
    diagnostics_module_name = "datetime"

    def get_initial(self):
        return {'is_enabled': self.service.is_enabled(),
                'is_running': self.service.is_running(),
                'time_zone': self.get_current_time_zone()}

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
                actions.superuser_run(
                    'timezone-change', [new_status['time_zone']])
            except Exception as exception:
                messages.error(
                    self.request, _('Error setting time zone: {exception}')
                    .format(exception=exception))
            else:
                messages.success(self.request, _('Time zone set'))

        return super().form_valid(form)
