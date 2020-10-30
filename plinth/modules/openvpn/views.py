# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring OpenVPN server.
"""

import logging

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import actions
from plinth.modules import config, openvpn
from plinth.views import AppView

logger = logging.getLogger(__name__)


class OpenVPNAppView(AppView):
    """Show OpenVPN app main page."""
    app_id = 'openvpn'
    template_name = 'openvpn.html'

    def dispatch(self, request, *args, **kwargs):
        """Collect the result of running setup process."""
        if bool(openvpn.setup_process):
            _collect_setup_result(request)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['status'] = {
            'is_setup': openvpn.is_setup(),
            'setup_running': bool(openvpn.setup_process),
        }
        context['refresh_page_sec'] = 3 if context['status'][
            'setup_running'] else None
        context['using_ecc'] = openvpn.is_using_ecc()
        return context


@require_POST
def setup(_):
    """Start the setup process."""
    if not openvpn.is_setup() and not openvpn.setup_process:
        openvpn.setup_process = actions.superuser_run('openvpn', ['setup'],
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


@require_POST
def ecc(_):
    """Migrate from RSA to ECC."""
    if openvpn.is_setup():
        openvpn.setup_process = actions.superuser_run('openvpn', ['setup'],
                                                      run_in_background=True)
    return redirect('openvpn:index')


def _collect_setup_result(request):
    """Handle setup process is completion."""
    if not openvpn.setup_process:
        return

    return_code = openvpn.setup_process.poll()

    # Setup process is not complete yet
    if return_code is None:
        return

    if not return_code:
        messages.success(request, _('Setup completed.'))
    else:
        messages.info(request, _('Setup failed.'))

    openvpn.setup_process = None
