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
Plinth module for service discovery views.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from .forms import ServiceDiscoveryForm
from plinth import actions
from plinth import package
from plinth.modules import avahi


logger = logging.getLogger(__name__)  # pylint: disable=C0103


@package.required(['avahi-daemon'])
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = ServiceDiscoveryForm(request.POST, prefix='avahi')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ServiceDiscoveryForm(initial=status, prefix='avahi')
    else:
        form = ServiceDiscoveryForm(initial=status, prefix='avahi')

    return TemplateResponse(request, 'avahi.html',
                            {'title': _('Service Discovery'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current settings from server."""
    return {'enabled': avahi.is_enabled(),
            'is_running': avahi.is_running()}


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        modified = True
        actions.superuser_run('avahi', [sub_command])
        avahi.service.notify_enabled(None, new_status['enabled'])
        messages.success(request, _('Configuration updated'))

    if not modified:
        messages.info(request, _('Setting unchanged'))
