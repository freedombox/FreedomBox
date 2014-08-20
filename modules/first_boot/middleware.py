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

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
import logging

import cfg
from withsqlite.withsqlite import sqlite_db


LOGGER = logging.getLogger(__name__)


class FirstBootMiddleware(object):
    """Forward to firstboot page if firstboot isn't finished yet."""

    @staticmethod
    def process_request(request):
        """Handle a request as Django middleware request handler."""
        # Prevent redirecting to first boot wizard in a loop by
        # checking if we are already in first boot wizard.
        if request.path.startswith(reverse('first_boot:index')):
            return

        with sqlite_db(cfg.store_file, table='firstboot') as database:
            if 'state' not in database:
                # Permanent redirect causes the browser to cache the redirect,
                # preventing the user from navigating to /plinth until the
                # browser is restarted.
                return HttpResponseRedirect(reverse('first_boot:index'))

            if database['state'] < 5:
                LOGGER.info('First boot state - %d', database['state'])
                return HttpResponseRedirect(reverse('first_boot:state%d' %
                                                    database['state']))
