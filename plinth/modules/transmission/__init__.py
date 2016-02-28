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
Plinth module to configure Transmission server
"""

from django.utils.translation import ugettext_lazy as _
import json
import socket

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


version = 1

depends = ['apps']

title = _('BitTorrent (Transmission)')

description = [
    _('BitTorrent is a peer-to-peer file sharing protocol. '
      'Transmission daemon handles Bitorrent file sharing.  Note that '
      'BitTorrent is not anonymous.')
]

service = None

TRANSMISSION_CONFIG = '/etc/transmission-daemon/settings.json'


def init():
    """Intialize the Transmission module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-save', 'transmission:index', 300)

    global service
    service = service_module.Service(
        'transmission', title, ['http', 'https'], is_external=True,
        enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['transmission-daemon'])

    new_configuration = {'rpc-whitelist-enabled': False}
    helper.call('post', actions.superuser_run, 'transmission',
                ['merge-configuration'],
                input=json.dumps(new_configuration).encode())

    helper.call('post', actions.superuser_run, 'transmission', ['enable'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current settings from Transmission server."""
    configuration = open(TRANSMISSION_CONFIG, 'r').read()
    status = json.loads(configuration)
    status = {key.translate(str.maketrans({'-': '_'})): value
              for key, value in status.items()}
    status['enabled'] = is_enabled()
    status['is_running'] = is_running()
    status['hostname'] = socket.gethostname()

    return status


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('transmission-daemon') and
            action_utils.webserver_is_enabled('transmission-plinth'))


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('transmission-daemon')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('transmission', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(9091, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(9091, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/transmission',
        extra_options=['--no-check-certificate']))

    return results
