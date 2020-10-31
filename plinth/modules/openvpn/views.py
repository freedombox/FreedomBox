# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring OpenVPN server.
"""

import logging

from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from plinth import actions
from plinth.modules import config, openvpn
from plinth.views import AppView

logger = logging.getLogger(__name__)


class OpenVPNAppView(AppView):
    """Show OpenVPN app main page."""
    app_id = 'openvpn'
    template_name = 'openvpn.html'

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['status'] = {
            'is_setup': openvpn.is_setup(),
        }
        context['using_ecc'] = openvpn.is_using_ecc()
        return context


@require_POST
def setup(_):
    """Start the setup process."""
    if not openvpn.is_setup():
        actions.superuser_run('openvpn', ['setup'], run_in_background=True)

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
        actions.superuser_run('openvpn', ['setup'], run_in_background=True)
    return redirect('openvpn:index')
