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
Plinth module to configure a Deluge web client.
"""

from gettext import gettext as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


depends = ['plinth.modules.apps']

service = None


def init():
    """Initialize the Deluge module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('BitTorrent (Deluge)'), 'glyphicon-magnet',
                     'deluge:index', 200)

    global service
    service = service_module.Service(
        'deluge', _('Deluge BitTorrent'), ['http', 'https'],
        is_external=True, enabled=is_enabled())


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.webserver_is_enabled('deluge-plinth') and
            action_utils.service_is_enabled('deluge-web'))


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('deluge-web')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(8112, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(8112, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/deluge', extra_options=['--no-check-certificate']))

    return results
