#
# This file is part of FreedomBox.
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
FreedomBox app for configuring OpenVPN server.
"""

import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import actions, daemon
from plinth.modules import config, openvpn

from .forms import OpenVpnForm

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

    return TemplateResponse(
        request, 'openvpn.html', {
            'app_id': 'openvpn',
            'app_info': openvpn.app.info,
            'port_forwarding_info': openvpn.port_forwarding_info,
            'status': status,
            'form': form,
            'show_status_block': True,
            'is_running': status['is_running'],
            'has_diagnostics': True,
            'is_enabled': status['enabled'],
        })


@require_POST
def setup(request):
    """Start the setup process."""
    global setup_process
    if not openvpn.is_setup() and not setup_process:
        setup_process = actions.superuser_run('openvpn', ['setup'],
                                              run_in_background=True)

    openvpn.app.enable()

    return redirect('openvpn:index')


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

    return {
        'is_setup': openvpn.is_setup(),
        'setup_running': bool(setup_process),
        'enabled': openvpn.app.is_enabled(),
        'is_running': daemon.app_is_running(openvpn.app)
    }


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
        if new_status['enabled']:
            openvpn.app.enable()
        else:
            openvpn.app.disable()

        modified = True

    if modified:
        messages.success(request, _('Configuration updated'))
    else:
        messages.info(request, _('Setting unchanged'))
