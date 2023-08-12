# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the Single Sign On app of FreedomBox."""

import logging
import os
import urllib

import axes.utils
from axes.decorators import axes_form_invalid
from django import shortcuts
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from plinth import translation, utils, web_framework

from . import privileged
from .forms import AuthenticationForm, CaptchaAuthenticationForm

PRIVATE_KEY_FILE_NAME = 'privkey.pem'
SSO_COOKIE_NAME = 'auth_pubtkt'
KEYS_DIRECTORY = '/etc/apache2/auth-pubtkt-keys'

logger = logging.getLogger(__name__)


def set_ticket_cookie(user, response):
    """Generate and set a mod_auth_pubtkt as a cookie in the response."""
    tokens = list(map(lambda g: g.name, user.groups.all()))
    private_key_file = os.path.join(KEYS_DIRECTORY, PRIVATE_KEY_FILE_NAME)
    ticket = privileged.generate_ticket(user.username, private_key_file,
                                        tokens)
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
        """Handle a request and return a HTTP response."""
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            translation.set_language(request, response,
                                     request.user.userprofile.language)
            return set_ticket_cookie(request.user, response)

        return response

    # XXX: Use axes middleware and authentication backend instead of
    # axes_form_invalid when axes >= 5.0.0 becomes available in Debian stable.
    @axes_form_invalid
    def form_invalid(self, *args, **kwargs):
        """Trigger django-axes logic to deal with too many attempts."""
        return super().form_invalid(*args, **kwargs)


class CaptchaLoginView(LoginView):
    """A login view with mandatory CAPTCHA image."""

    redirect_authenticated_user = True
    template_name = 'login.html'
    form_class = CaptchaAuthenticationForm

    def dispatch(self, request, *args, **kwargs):
        """Handle a request and return a HTTP response."""
        response = super().dispatch(request, *args, **kwargs)
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


@require_POST
def logout(request):
    """Logout an authenticated user, remove SSO cookie and redirect to home."""
    auth_logout(request)
    response = shortcuts.redirect('index')
    response.delete_cookie(SSO_COOKIE_NAME)
    messages.success(request, _('Logged out successfully.'))
    return response


def refresh(request):
    """Simulate cookie refresh - redirect logged in user with a new cookie."""
    redirect_url = request.GET.get(REDIRECT_FIELD_NAME, '')
    response = HttpResponseRedirect(redirect_url)
    response.delete_cookie(SSO_COOKIE_NAME)
    # Redirect with cookie doesn't work with 300 series
    response.status_code = 200
    return set_ticket_cookie(request.user, response)
