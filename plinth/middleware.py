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
Common Django middleware.
"""

from django import urls
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
import logging

from stronghold.utils import is_view_func_public

import plinth
from plinth import setup
from plinth.package import PackageException
from plinth.utils import is_user_admin
from . import views

logger = logging.getLogger(__name__)


class SetupMiddleware(object):
    """Django middleware to show pre-setup message and setup progress."""

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """Handle a request as Django middleware request handler."""
        # Don't interfere with login page
        user_requests_login = request.path.startswith(
            urls.reverse(settings.LOGIN_URL))
        if user_requests_login:
            return

        # Perform a URL resolution. This is slightly inefficient as
        # Django will do this resolution again.
        try:
            resolver_match = urls.resolve(request.path_info)
        except urls.Resolver404:
            return

        if not resolver_match.namespaces or not len(resolver_match.namespaces):
            # Requested URL does not belong to any application
            return

        module_name = resolver_match.namespaces[0]
        module = plinth.module_loader.loaded_modules[module_name]

        # Collect errors from any previous operations and show them
        if module.setup_helper.is_finished:
            exception = module.setup_helper.collect_result()
            if not exception:
                messages.success(request, _('Application installed.'))
            else:
                if isinstance(exception, PackageException):
                    error_string = getattr(exception, 'error_string',
                                           str(exception))
                    error_details = getattr(exception, 'error_details', '')
                    message = _('Error installing application: {string} '
                                '{details}').format(
                                    string=error_string, details=error_details)
                else:
                    message = _('Error installing application: {error}') \
                        .format(error=exception)

                messages.error(request, message)

        # Check if application is up-to-date
        if module.setup_helper.get_state() == 'up-to-date':
            return

        # Only allow logged-in users to access any setup page
        view = login_required(views.SetupView.as_view())
        return view(request, setup_helper=module.setup_helper)


class AdminRequiredMiddleware(object):
    """Django middleware for authenticating requests for admin areas."""

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """Reject non-admin access to views that are private and not marked."""
        if is_view_func_public(view_func) or \
           hasattr(view_func, 'IS_NON_ADMIN'):
            return

        if not is_user_admin(request):
            raise PermissionDenied


class FirstSetupMiddleware(object):

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """Block all user interactions when first setup is pending."""
        if not setup.is_first_setup_running:
            return

        context = {'is_first_setup_running': setup.is_first_setup_running}
        return render(request, 'first_setup.html', context)
