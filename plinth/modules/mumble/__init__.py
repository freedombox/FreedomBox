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
Plinth module to configure Mumble server
"""

from gettext import gettext as _

from plinth import actions
from plinth import cfg
from plinth import service as service_module


depends = ['plinth.modules.apps']

service = None


def init():
    """Intialize the Mumble module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Voice Chat (Mumble)'), 'glyphicon-headphones',
                     'mumble:index', 50)

    output = actions.run('mumble', ['get-enabled'])
    enabled = (output.strip() == 'yes')

    global service
    service = service_module.Service(
        'mumble-plinth', _('Mumble Voice Chat Server'),
        is_external=True, enabled=enabled)
