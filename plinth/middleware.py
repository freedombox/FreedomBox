# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Common Django middleware.
"""

import logging

from django import urls
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import ugettext_lazy as _
from stronghold.utils import is_view_func_public

import plinth
from plinth import setup
from plinth.package import PackageException
from plinth.utils import is_user_admin

from . import views

logger = logging.getLogger(__name__)


class SetupMiddleware(MiddlewareMixin):
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
                if not setup._is_module_essential(module):
                    messages.success(request, _('Application installed.'))
            else:
                if isinstance(exception, PackageException):
                    error_string = getattr(exception, 'error_string',
                                           str(exception))
                    error_details = getattr(exception, 'error_details', '')
                    message = _('Error installing application: {string} '
                                '{details}').format(string=error_string,
                                                    details=error_details)
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


class AdminRequiredMiddleware(MiddlewareMixin):
    """Django middleware for authenticating requests for admin areas."""

    @staticmethod
    def check_user_group(view_func, request):
        if hasattr(view_func, 'GROUP_NAME'):
            return request.user.groups.filter(
                name=getattr(view_func, 'GROUP_NAME')).exists()

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """Reject non-admin access to views that are private and not marked."""
        if is_view_func_public(view_func) or \
           hasattr(view_func, 'IS_NON_ADMIN'):
            return

        if not is_user_admin(request):
            if not AdminRequiredMiddleware.check_user_group(
                    view_func, request):
                raise PermissionDenied


class FirstSetupMiddleware(MiddlewareMixin):
    """Django middleware to block all interactions before first setup."""

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """Block all user interactions when first setup is pending."""
        if not setup.is_first_setup_running:
            return

        context = {'is_first_setup_running': setup.is_first_setup_running}
        return render(request, 'first_setup.html', context)
