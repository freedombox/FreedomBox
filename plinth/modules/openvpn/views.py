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
Plinth module for configuring OpenVPN server.
"""

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
import logging

from .forms import OpenVpnForm
from plinth import actions
from plinth.modules import openvpn
from plinth.modules.config import config

logger = logging.getLogger(__name__)

setup_process = None


def index(request):
    """Serve configuration page."""
    status = get_status()

    if status['setup_running']:
        _collect_setup_result(request)

    form = None

    if request.method == 'POST':
        form = OpenVpnForm(request.POST, prefix='openvpn')
        # pylint: disable=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = OpenVpnForm(initial=status, prefix='openvpn')
    else:
        form = OpenVpnForm(initial=status, prefix='openvpn')

    return TemplateResponse(request, 'openvpn.html',
                            {'title': openvpn.title,
                             'description': openvpn.description,
                             'status': status,
                             'form': form})


@require_POST
def setup(request):
    """Start the setup process."""
    openvpn.service.notify_enabled(None, True)

    global setup_process
    if not openvpn.is_setup() and not setup_process:
        setup_process = actions.superuser_run('openvpn', ['setup'], async=True)

    return redirect('openvpn:index')


@require_POST
def profile(request):
    """Provide the user's profile for download."""
    username = request.user.username
    domainname = config.get_domainname()

    if not config.get_domainname():
        domainname = config.get_hostname()

    profile_string = actions.superuser_run(
        'openvpn', ['get-profile', username, domainname])

    response = HttpResponse(profile_string,
                            content_type='application/x-openvpn-profile')
    response['Content-Disposition'] = \
        'attachment; filename={username}.ovpn'.format(username=username)

    return response


def get_status():
    """Get the current settings from OpenVPN server."""
    status = {'is_setup': openvpn.is_setup(),
              'setup_running': False,
              'enabled': openvpn.is_enabled(),
              'is_running': openvpn.is_running()}

    status['setup_running'] = bool(setup_process)

    return status


def _collect_setup_result(request):
    """Handle setup process is completion."""
    global setup_process
    if not setup_process:
        return

    return_code = setup_process.poll()

    # Setup process is not complete yet
    if return_code is None:
        return

    if not return_code:
        messages.success(request, _('Setup completed.'))
    else:
        messages.info(request, _('Setup failed.'))

    setup_process = None


def _apply_changes(request, old_status, new_status):
    """Apply the changes."""
    modified = False

    if old_status['enabled'] != new_status['enabled']:
        sub_command = 'enable' if new_status['enabled'] else 'disable'
        actions.superuser_run('openvpn', [sub_command])
        openvpn.service.notify_enabled(None, new_status['enabled'])
        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
