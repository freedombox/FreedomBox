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
Plinth module to configure Tiny Tiny RSS
"""

from gettext import gettext as _

from plinth import cfg
from plinth import action_utils

def init():
    """Intialize  Tiny Tiny RSS module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('News Feed Reader (Tiny Tiny RSS)'), 'glyphicon-envelope',
                     'ttrss:index', 600)

depends = ['plinth.modules.apps']

def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('50-tt-rss')

def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/ttrss', extra_options=['--no-check-certificate']))

    return results
