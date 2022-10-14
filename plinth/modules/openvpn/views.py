# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring OpenVPN server."""

import logging

from django.http import HttpResponse

from plinth.modules import config
from plinth.views import AppView

from . import privileged

logger = logging.getLogger(__name__)


class OpenVPNAppView(AppView):
    """Show OpenVPN app main page."""

    app_id = 'openvpn'
    template_name = 'openvpn.html'


def profile(request):
    """Provide the user's profile for download."""
    username = request.user.username
    domainname = config.get_domainname()

    if not config.get_domainname():
        domainname = config.get_hostname()

    profile_string = privileged.get_profile(username, domainname)
    response = HttpResponse(profile_string,
                            content_type='application/x-openvpn-profile')
    response['Content-Disposition'] = \
        'attachment; filename={username}.ovpn'.format(username=username)

    return response
