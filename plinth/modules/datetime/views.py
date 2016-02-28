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
from plinth import views
from plinth.modules import datetime

logger = logging.getLogger(__name__)


class ConfigurationView(views.ConfigurationView):
    """Serve configuration page."""
    form_class = DateTimeForm

    def apply_changes(self, old_status, new_status):
        """Apply the changes."""
        modified = False

        if old_status['enabled'] != new_status['enabled']:
            sub_command = 'enable' if new_status['enabled'] else 'disable'
            modified = True
            actions.superuser_run('datetime', [sub_command])
            datetime.service.notify_enabled(None, new_status['enabled'])
            messages.success(self.request, _('Configuration updated'))

        if old_status['time_zone'] != new_status['time_zone'] and \
           new_status['time_zone'] != 'none':
            modified = True
            try:
                actions.superuser_run(
                    'timezone-change', [new_status['time_zone']])
            except Exception as exception:
                messages.error(
                    self.request, _('Error setting time zone: {exception}')
                    .format(exception=exception))
            else:
                messages.success(self.request, _('Time zone set'))

        return modified
