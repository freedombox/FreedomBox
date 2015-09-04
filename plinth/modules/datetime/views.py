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
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from .forms import DateTimeForm
from plinth import actions
from plinth import package
from plinth.modules import datetime

logger = logging.getLogger(__name__)


def on_install():
    """Notify that the service is now enabled."""
    datetime.service.notify_enabled(None, True)


@package.required(['ntp'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = DateTimeForm(request.POST, prefix='datetime')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = DateTimeForm(initial=status, prefix='datetime')
    else:
        form = DateTimeForm(initial=status, prefix='datetime')

    return TemplateResponse(request, 'datetime.html',
                            {'title': _('Date & Time'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current settings from server."""
    return {'enabled': datetime.is_enabled(),
            'is_running': datetime.is_running(),
            'time_zone': get_current_time_zone()}


def get_current_time_zone():
    """Get current time zone."""
    time_zone = open('/etc/timezone').read().rstrip()
    return time_zone or 'none'


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        modified = True
        actions.superuser_run('datetime', [sub_command])
        datetime.service.notify_enabled(None, new_status['enabled'])
        messages.success(request, _('Configuration updated'))

    if old_status['time_zone'] != new_status['time_zone'] and \
       new_status['time_zone'] != 'none':
        modified = True
        try:
            actions.superuser_run('timezone-change', [new_status['time_zone']])
        except Exception as exception:
            messages.error(request, _('Error setting time zone: %s') %
                           exception)
        else:
            messages.success(request, _('Time zone set'))

    if not modified:
        messages.info(request, _('Setting unchanged'))
