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
Plinth module for configuring Privoxy Server.
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
import logging

from .forms import PrivoxyForm
from plinth import actions
from plinth import package
from plinth.modules import privoxy

logger = logging.getLogger(__name__)


def on_install():
    """Notify that the service is now enabled."""
    actions.superuser_run('privoxy', ['setup'])
    privoxy.service.notify_enabled(None, True)


@package.required(['privoxy'], on_install=on_install)
def index(request):
    """Serve configuration page."""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = PrivoxyForm(request.POST, prefix='privoxy')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = PrivoxyForm(initial=status, prefix='privoxy')
    else:
        form = PrivoxyForm(initial=status, prefix='privoxy')

    return TemplateResponse(request, 'privoxy.html',
                            {'title': _('Web Proxy (Privoxy)'),
                             'status': status,
                             'form': form})


def get_status():
    """Get the current settings from server."""
    status = {'enabled': privoxy.is_enabled(),
              'is_running': privoxy.is_running()}

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('privoxy', [sub_command])
        privoxy.service.notify_enabled(None, new_status['enabled'])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
