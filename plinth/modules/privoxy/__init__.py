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
Plinth module to configure Privoxy.
"""

from gettext import gettext as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


depends = ['plinth.modules.apps']

service = None


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Web Proxy (Privoxy)'), 'glyphicon-cloud-upload',
                     'privoxy:index', 1000)

    global service
    service = service_module.Service(
        'privoxy', _('Privoxy Web Proxy'),
        is_external=False, enabled=is_enabled())


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('privoxy')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('privoxy')
