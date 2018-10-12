#
# This file is part of FreedomBox.
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
Django middleware to occasionally delete temporary backup files
"""

import logging
import random
import time

from django.utils.deprecation import MiddlewareMixin

from plinth.modules import backups

LOGGER = logging.getLogger(__name__)


class BackupsMiddleware(MiddlewareMixin):
    """Delete outdated backup file."""

    @staticmethod
    def process_request(request):
        """Handle a request as Django middleware request handler."""
        if random.random() > 0.9:
            if request.session.has_key(backups.SESSION_BACKUP_VARIABLE):
                now = time.time()
                if now > request.session[backups.SESSION_BACKUP_VARIABLE]:
                    backups.delete_upload_backup_file()
                    del request.session[backups.SESSION_BACKUP_VARIABLE]
            else:
                backups.delete_upload_backup_file()
        return
