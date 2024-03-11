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
from django.db.utils import OperationalError
from django.shortcuts import render
from django.template.response import SimpleTemplateResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext as _
from stronghold.utils import is_view_func_public

from plinth import app as app_module
from plinth import setup
from plinth.utils import is_user_admin

from . import operation as operation_module
from . import views

logger = logging.getLogger(__name__)


def _collect_operations_results(request, app):
    """Show success/fail messages from previous operations."""
    operations = operation_module.manager.collect_results(app.app_id)
    for operation in operations:
        if operation.exception:
            views.messages_error(request, operation.message,
                                 operation.exception)
        else:
            messages.success(request, operation.message)


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

        app_id = resolver_match.namespaces[0]
        app = app_module.App.get(app_id)

        is_admin = is_user_admin(request)
        # Collect and show operations' results to admins
        if is_admin:
            _collect_operations_results(request, app)

        # Check if application is up-to-date
        if app.get_setup_state() == \
           app_module.App.SetupState.UP_TO_DATE:
            return

        if not is_admin:
            raise PermissionDenied

        # Only allow logged-in users to access any setup page
        view = login_required(views.SetupView.as_view())
        return view(request, app_id=app_id)


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

        context = {
            'is_first_setup_running': setup.is_first_setup_running,
            'refresh_page_sec': 3
        }
        return render(request, 'first_setup.html', context)


class CommonErrorMiddleware(MiddlewareMixin):
    """Django middleware to handle common errors."""

    @staticmethod
    def process_exception(request, exception):
        """Show a custom error page when OperationalError is raised."""
        if isinstance(exception, OperationalError):
            message = _(
                'System is possibly under heavy load. Please retry later.')
            return SimpleTemplateResponse('error.html',
                                          context={'message': message},
                                          status=503)

        return None
