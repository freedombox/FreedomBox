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
Main Plinth views
"""

from django.http.response import HttpResponseRedirect
import os
import stat

import cfg
from withsqlite.withsqlite import sqlite_db


def index(request):
    """Serve the main index page"""
    # TODO: Move firstboot handling to firstboot module somehow
    with sqlite_db(cfg.store_file, table='firstboot') as database:
        if not 'state' in database:
            # If we created a new user db, make sure it can't be read by
            # everyone
            userdb_fname = '{}.sqlite3'.format(cfg.user_db)
            os.chmod(userdb_fname, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            # Permanent redirect causes the browser to cache the redirect,
            # preventing the user from navigating to /plinth until the
            # browser is restarted.
            return HttpResponseRedirect(cfg.server_dir + '/firstboot')

        if database['state'] < 5:
            cfg.log('First boot state = %d' % database['state'])
            return HttpResponseRedirect(
                cfg.server_dir + '/firstboot/state%d' % database['state'])

    if request.session.get(cfg.session_key, None):
        return HttpResponseRedirect(cfg.server_dir + '/apps')

    return HttpResponseRedirect(cfg.server_dir + '/help/about')
