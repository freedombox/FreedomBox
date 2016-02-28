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

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


version = 1

depends = ['apps']

title = _('Voice Chat (Mumble)')

description = [
    _('Mumble is an open source, low-latency, encrypted, high quality '
      'voice chat software.'),

    _('You can connect to your Mumble server on the regular Mumble port '
      '64738. <a href="http://mumble.info">Clients</a> to connect to Mumble '
      'from your desktop and Android devices are available.')
]

service = None


def init():
    """Intialize the Mumble module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-headphones', 'mumble:index', 900)

    global service
    service = service_module.Service(
        'mumble-plinth', title, is_external=True, enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['mumble-server'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current settings from server."""
    return {'enabled': is_enabled(),
            'is_running': is_running()}


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('mumble-server')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('mumble-server')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('mumble', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(64738, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp6'))

    return results
