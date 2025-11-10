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
from django.http import Http404, HttpResponseNotAllowed
from django.shortcuts import redirect, render
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
            views.messages_error(request, operation.translated_message,
                                 operation.exception)
        else:
            messages.success(request, operation.translated_message)


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
        logger.exception('Error processing page. %s %s, exception: %s',
                         request.method, request.path, exception)
        if isinstance(exception, OperationalError):
            message = _(
                'System is possibly under heavy load. Please retry later.')
            return SimpleTemplateResponse('error.html',
                                          context={'message': message},
                                          status=503)

        if isinstance(exception, Exception):
            match = request.resolver_match
            if not match.app_name and match.url_name == 'index':
                # Don't try to handle errors on the home page as it will lead
                # to infinite redirects.
                return None

            if isinstance(exception, Http404):
                message = _('Page not found: {url}').format(url=request.path)
                exception = None  # Don't show exception details
            elif request.method == 'POST':
                message = _('Error running operation.')
            else:
                message = _('Error loading page.')

            if exception:
                views.messages_error(request, message, exception)
            else:
                messages.error(request, message)

            redirect_url = CommonErrorMiddleware._get_redirect_url_on_error(
                request)
            return redirect(redirect_url)

        return None

    @staticmethod
    def process_response(request, response):
        """Handle 405 method not allowed errors.

        These errors may happen when we redirect to a page that does not allow
        GET.
        """
        if isinstance(response, HttpResponseNotAllowed):
            redirect_url = CommonErrorMiddleware._get_redirect_url_on_error(
                request)
            return redirect(redirect_url)

        return response

    @staticmethod
    def _get_redirect_url_on_error(request):
        """Return the URL to redirect to after an error."""
        if request.method != 'GET':
            return request.path

        # If the original request was a GET, trying to redirect to same URL
        # with same request method might result in an recursive loop. Instead
        # redirect to a parent URL.
        breadcrumbs = views.get_breadcrumbs(request)
        parent_index = 1 if len(breadcrumbs) > 1 else 0
        return list(breadcrumbs.keys())[parent_index]


class CSPDict(dict):
    """A dictionary to store Content Security Policy.

    And return a full value of the HTTP header.
    """

    def get_header_value(self) -> str:
        """Return the string header value for the policy stored."""
        return ' '.join([f'{key} {value};' for key, value in self.items()])


CONTENT_SECURITY_POLICY = CSPDict({
    # @fonts are allowed only from FreedomBox itself.
    'font-src': "'self'",
    # <frame>/<iframe> sources are disabled.
    'frame-src': "'none'",
    # <img> sources are allowed only from FreedomBox itself. Allow
    # data: URLs for SVGs in CSS.
    'img-src': "'self' data:",
    # Manifest file is not allowed as there is none yet.
    'manifest-src': "'none'",
    # <audio>, <video>, <track> tags are not allowed yet.
    'media-src': "'none'",
    # <object>, <embed>, <applet> tags are not allowed yet. No plugins
    # types are alllowed since object-src is 'none'.
    'object-src': "'none'",
    # Allow JS from FreedomBox itself (no inline and attribute
    # scripts).
    'script-src': "'self'",
    # Allow inline CSS and CSS files from Freedombox itself.
    'style-src': "'self'",
    # Web worker sources are allowed only from FreedomBox itself (for
    # JSXC).
    'worker-src': "'self'",
    # All other fetch sources including Ajax are not allowed from
    # FreedomBox itself.
    'default-src': "'self'",
    # <base> tag is not allowed.
    'base-uri': "'none'",
    # Enable strict sandboxing enabled with some exceptions:
    # - Allow running Javascript.
    # - Allow popups as sometimes we use <a target=_blank>
    # - Allow popups to have different sandbox requirements as we
    #   launch apps' web clients.
    # - Allow forms to support configuration forms.
    # - Allow policies to treat same origin differently from other
    # - origins
    # - Allow downloads such as backup tarballs.
    'sandbox': 'allow-scripts allow-popups '
               'allow-popups-to-escape-sandbox allow-forms '
               'allow-same-origin allow-downloads',
    # Form action should be to FreedomBox itself.
    'form-action': "'self'",
    # This interface may be not embedded in <frame>, <iframe>, etc.
    # tags.
    'frame-ancestors': "'none'",
})


class CommonHeadersMiddleware:

    def __init__(self, get_response):
        """Initialize the middleware object."""
        self.get_response = get_response

    def __call__(self, request):
        """Add common security middleware."""
        # Disable sending Referer (sic) header from FreedomBox web interface to
        # external websites. This improves privacy by not disclosing FreedomBox
        # domains/URLs to external domains. Apps such as blogs which want to
        # popularize themselves with referrer header may still do so.
        response = self.get_response(request)
        if not response.get('Referrer-Policy'):
            response['Referrer-Policy'] = 'same-origin'

        # Disable browser guessing of MIME types. FreedoBox already sets good
        # content types for all the common file types.
        if not response.get('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'

        csp = ' '.join([
            f'{key} {value};'
            for key, value in CONTENT_SECURITY_POLICY.items()
        ])
        if not response.get('Content-Security-Policy'):
            response['Content-Security-Policy'] = csp

        return response
