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
Plinth module to configure OpenVPN server.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


depends = ['plinth.modules.apps']

service = None


def init():
    """Intialize the OpenVPN module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Virtual Private Network (OpenVPN)'), 'glyphicon-lock',
                     'openvpn:index', 850)

    global service
    service = service_module.Service(
        'openvpn', _('OpenVPN'), ['openvpn'],
        is_external=True, enabled=is_enabled())


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('openvpn@freedombox')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('openvpn@freedombox')


def is_setup():
    """Return whether the service is running."""
    return actions.superuser_run('openvpn', ['is-setup']).strip() == 'true'


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(1194, 'udp4'))

    return results
