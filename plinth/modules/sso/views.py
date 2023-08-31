# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the Single Sign On app of FreedomBox."""

import logging
import os
import urllib

import axes.utils
from django import shortcuts
from django.contrib import messages
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView

from plinth import translation

from . import privileged
from .forms import AuthenticationForm, CaptchaForm

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


class CaptchaView(FormView):
    """A simple form view with a CAPTCHA image.

    When a user performs too many login attempts, they will no longer be able
    to login with the typical login view. They will be redirected to this view.
    On successfully solving the CAPTCHA in this form, their ability to use the
    login form will be reset.
    """

    template_name = 'captcha.html'
    form_class = CaptchaForm

    def form_valid(self, form):
        """Reset login attempts and redirect to login page."""
        axes.utils.reset_request(self.request)
        return shortcuts.redirect('users:login')


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
