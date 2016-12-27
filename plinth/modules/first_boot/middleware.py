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
Django middleware to redirect to firstboot wizard if it has not be run
yet.
"""

from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.conf import settings
import logging

from plinth.modules import first_boot

LOGGER = logging.getLogger(__name__)


class FirstBootMiddleware(object):
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

        firstboot_completed = first_boot.is_completed()
        user_requests_firstboot = first_boot.is_firstboot_url(request.path)

        # Redirect to first boot if requesting normal page and first
        # boot is not complete.
        if not firstboot_completed and not user_requests_firstboot:
            next_step = first_boot.next_step_or_none()
            if next_step:
                return HttpResponseRedirect(reverse(next_step))
            else:
                # No more steps in first boot
                first_boot.set_completed()

        # Redirect to index page if request firstboot after it is
        # finished.
        if firstboot_completed and user_requests_firstboot:
            return HttpResponseRedirect(reverse('index'))
