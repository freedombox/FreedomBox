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

from plinth import actions
from plinth import action_utils
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu


version = 1

managed_services = ['transmission-daemon']

managed_packages = ['transmission-daemon']

title = _('BitTorrent \n (Transmission)')

description = [
    _('BitTorrent is a peer-to-peer file sharing protocol. '
      'Transmission daemon handles Bitorrent file sharing.  Note that '
      'BitTorrent is not anonymous.'),
    _('Access the web interface at <a href="/transmission">/transmission</a>.')
]

reserved_usernames = ['debian-transmission']

service = None


def init():
    """Intialize the Transmission module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-save', 'transmission:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['http', 'https'],
            is_external=True, is_enabled=is_enabled,
            enable=enable, disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)

    new_configuration = {'rpc-whitelist-enabled': False}
    helper.call('post', actions.superuser_run, 'transmission',
                ['merge-configuration'],
                input=json.dumps(new_configuration).encode())

    helper.call('post', actions.superuser_run, 'transmission', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['http', 'https'],
            is_external=True, is_enabled=is_enabled,
            enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut(
            'transmission', title, url='/transmission',
            login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('transmission-daemon') and
            action_utils.webserver_is_enabled('transmission-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('transmission', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('transmission', ['disable'])
    frontpage.remove_shortcut('transmission')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(9091, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(9091, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/transmission', check_certificate=False))

    return results
