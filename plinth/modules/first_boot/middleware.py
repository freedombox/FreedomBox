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
import logging

from plinth import kvstore


LOGGER = logging.getLogger(__name__)


class FirstBootMiddleware(object):
    """Forward to firstboot page if firstboot isn't finished yet."""

    @staticmethod
    def process_request(request):
        """Handle a request as Django middleware request handler."""
        state = kvstore.get_default('firstboot_state', 0)

        firstboot_index_url = reverse('first_boot:index')
        user_requests_firstboot = request.path.startswith(firstboot_index_url)

        help_index_url = reverse('help:index')
        user_requests_help = request.path.startswith(help_index_url)

        # Setup is complete: Forbid accessing firstboot
        if state >= 10 and user_requests_firstboot:
            return HttpResponseRedirect(reverse('index'))

        # Setup is not complete: Forbid accessing anything but
        # firstboot or help
        if state < 10 and not user_requests_firstboot and \
           not user_requests_help:
            return HttpResponseRedirect(reverse('first_boot:state%d' % state))
