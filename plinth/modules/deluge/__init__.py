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

from django.utils.translation import ugettext_lazy as _
from functools import partial

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


version = 1

depends = ['apps']

title = _('BitTorrent Web Client (Deluge)')

description = [
    _('Deluge is a BitTorrent client that features a Web UI.'),

    _('When enabled, the Deluge web client will be available from '
      '<a href="/deluge">/deluge</a> path on the web server. The '
      'default password is \'deluge\', but you should log in and change '
      'it immediately after enabling this service.')
]

service = None

managed_services = ['deluge-web']


def init():
    """Initialize the Deluge module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-magnet', 'deluge:index', 200)

    global service
    service = service_module.Service(
        managed_services[0], title, ports=['http', 'https'], is_external=True,
        is_enabled=is_enabled, enable=_enable, disable=_disable)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['deluged', 'deluge-web'])
    helper.call('post', actions.superuser_run, 'deluge', ['enable'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current settings."""
    return {'enabled': service.is_enabled(),
            'is_running': service.is_running()}


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.webserver_is_enabled('deluge-plinth') and
            action_utils.service_is_enabled('deluge-web'))


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('deluge', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(8112, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(8112, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/deluge', extra_options=['--no-check-certificate']))

    return results


_enable = partial(enable, True)
_disable = partial(enable, False)
