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
Views for the Single Sign On app of FreedomBox.
"""

import logging
import os
import urllib

import axes.utils
from axes.decorators import axes_form_invalid
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect

from plinth import actions, utils, web_framework

from .forms import AuthenticationForm, CaptchaAuthenticationForm

PRIVATE_KEY_FILE_NAME = 'privkey.pem'
SSO_COOKIE_NAME = 'auth_pubtkt'
KEYS_DIRECTORY = '/etc/apache2/auth-pubtkt-keys'

logger = logging.getLogger(__name__)


def set_ticket_cookie(user, response):
    """Generate and set a mod_auth_pubtkt as a cookie in the provided
    response.
    """
    tokens = list(map(lambda g: g.name, user.groups.all()))
    private_key_file = os.path.join(KEYS_DIRECTORY, PRIVATE_KEY_FILE_NAME)
    ticket = actions.superuser_run('auth-pubtkt', [
        'generate-ticket', '--uid', user.username, '--private-key-file',
        private_key_file, '--tokens', ','.join(tokens)
    ])
    response.set_cookie(SSO_COOKIE_NAME, urllib.parse.quote(ticket))
    return response


class SSOLoginView(LoginView):
    """View to login to FreedomBox and set a auth_pubtkt cookie.

    Cookie will be used to provide Single Sign On for some other applications.

    """
    redirect_authenticated_user = True
    template_name = 'login.html'
    form_class = AuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        response = super(SSOLoginView, self).dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            return set_ticket_cookie(request.user, response)

        return response

    # XXX: Use axes middleware and authentication backend instead of
    # axes_form_invalid when axes >= 5.0.0 becomes available in Debian stable.
    @axes_form_invalid
    def form_invalid(self, *args, **kwargs):
        return super(SSOLoginView, self).form_invalid(*args, **kwargs)


class CaptchaLoginView(LoginView):
    redirect_authenticated_user = True
    template_name = 'login.html'
    form_class = CaptchaAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        response = super(CaptchaLoginView,
                         self).dispatch(request, *args, **kwargs)
        if not request.POST:
            return response

        if not request.user.is_authenticated:
            return response

        # Successful authentication
        if utils.is_axes_old():
            ip_address = web_framework.get_ip_address_from_request(request)
            axes.utils.reset(ip=ip_address)
            logger.info(
                'Login attempts reset for IP after successful login: %s',
                ip_address)

        return set_ticket_cookie(request.user, response)


class SSOLogoutView(LogoutView):
    """View to log out of FreedomBox and remove the auth_pubtkt cookie."""
    template_name = 'index.html'

    def dispatch(self, request, *args, **kwargs):
        response = super(SSOLogoutView, self).dispatch(request, *args,
                                                       **kwargs)
        response.delete_cookie(SSO_COOKIE_NAME)
        return response


def refresh(request):
    """Simulate cookie refresh - redirect logged in user with a new cookie"""
    redirect_url = request.GET.get(REDIRECT_FIELD_NAME, '')
    response = HttpResponseRedirect(redirect_url)
    response.delete_cookie(SSO_COOKIE_NAME)
    # Redirect with cookie doesn't work with 300 series
    response.status_code = 200
    return set_ticket_cookie(request.user, response)
