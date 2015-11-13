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
Plinth module for service discovery.
"""

from django.utils.translation import ugettext_lazy as _
import subprocess

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module

# pylint: disable=C0103

depends = ['plinth.modules.system']

service = None


def init():
    """Intialize the service discovery module."""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Service Discovery'), 'glyphicon-lamp',
                     'avahi:index', 950)

    global service  # pylint: disable=W0603
    service = service_module.Service(
        'avahi', _('Service Discovery'), ['mdns'],
        is_external=False, enabled=is_enabled())


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('avahi-daemon')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('avahi-daemon')
