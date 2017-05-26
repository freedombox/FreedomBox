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
Views for the Single Sign On module of Plinth
"""

import os
import urllib

from plinth.modules.sso import generate_ticket

from django.http import HttpResponseRedirect
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (login as auth_login,
                                       logout as auth_logout)


PRIVATE_KEY_FILE_NAME = 'privkey.pem'
SSO_COOKIE_NAME = 'auth_pubtkt'
KEYS_DIRECTORY = '/usr/share/sso-keys'


def set_ticket_cookie(username, response):
    """Generate and set a mod_auth_pubtkt as a cookie in the provided
    response.
    """
    ticket = generate_ticket(username,
                             os.path.join(KEYS_DIRECTORY,
                                          PRIVATE_KEY_FILE_NAME), list())
    ticket = urllib.parse.quote(ticket)
    response.set_cookie(SSO_COOKIE_NAME, ticket)
    return response


def login(request):
    """Login to Plinth and set a auth_pubtkt cookie which will be
    used to provide Single Sign On for some other applications
    """
    response = auth_login(
        request, template_name='login.html', redirect_authenticated_user=True)

    if request.user.is_authenticated:
        return set_ticket_cookie(request.user.username, response)
    else:
        return response


def logout(request, next_page):
    """Log out of Plinth and remove auth_pubtkt cookie"""
    response = auth_logout(request, next_page=next_page)
    response.delete_cookie(SSO_COOKIE_NAME)
    return response


@login_required
def refresh(request):
    """Simulate cookie refresh - redirect logged in user with a new cookie"""
    redirect_url = request.GET.get(REDIRECT_FIELD_NAME, '')
    response = HttpResponseRedirect(redirect_url)
    response.delete_cookie(SSO_COOKIE_NAME)
    return set_ticket_cookie(request.user.username, response)
