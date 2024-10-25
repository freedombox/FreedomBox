# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django middleware to redirect to firstboot wizard if it has not be run
yet.
"""

import logging

from django.conf import settings
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from plinth import setup
from plinth.modules import first_boot
from plinth.utils import is_user_admin

LOGGER = logging.getLogger(__name__)


class FirstBootMiddleware(MiddlewareMixin):
    """Forward to firstboot page if firstboot isn't finished yet."""

    @staticmethod
    def process_request(request):
        """Handle a request as Django middleware request handler."""
        # Don't interfere with login page
        user_requests_login = request.path.startswith(
            reverse(settings.LOGIN_URL))
        if user_requests_login:
            return

        # Don't interfere with help pages
        user_requests_help = request.path.startswith(reverse('help:index'))
        if user_requests_help:
            return

        # Don't interfere with first setup progress page. When first setup is
        # still running, no apps may have provided the first boot steps. This
        # will result in first boot wizard getting marked as completed
        # prematurely.
        if setup.is_first_setup_running:
            return

        firstboot_completed = first_boot.is_completed()
        user_requests_firstboot = first_boot.is_firstboot_url(request.path)

        # If user requests a step other than the welcome step, verify that they
        # indeed completed the secret verification by looking at the session.
        if (user_requests_firstboot
                and not request.path.startswith(reverse('first_boot:welcome'))
                and first_boot.firstboot_wizard_secret_exists()
                and not request.session.get('firstboot_secret_provided', False)
                and not is_user_admin(request)):
            return HttpResponseRedirect(reverse('first_boot:welcome'))

        # Redirect to first boot if requesting normal page and first
        # boot is not complete.
        if not firstboot_completed and not user_requests_firstboot:
            next_step = first_boot.next_step_or_none()
            if next_step:
                return HttpResponseRedirect(reverse(next_step))
            else:
                # No more steps in first boot
                first_boot.set_completed()

        # Redirect to 'complete' page if user requested firstboot after it is
        # finished.
        if firstboot_completed and user_requests_firstboot:
            return HttpResponseRedirect(reverse('first_boot:complete'))
