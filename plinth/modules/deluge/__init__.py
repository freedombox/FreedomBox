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

from plinth import actions
from plinth import action_utils
from plinth import frontpage
from plinth import service as service_module
from plinth.client import web_client
from plinth.menu import main_menu
from plinth.modules.users import create_group, register_group


version = 2

service = None

managed_services = ['deluge-web']

managed_packages = ['deluged', 'deluge-web']

name = _('Deluge')

short_description = _('BitTorrent Web Client')

description = [
    _('Deluge is a BitTorrent client that features a Web UI.'),

    _('When enabled, the Deluge web client will be available from '
      '<a href="/deluge">/deluge</a> path on the web server. The '
      'default password is \'deluge\', but you should log in and change '
      'it immediately after enabling this service.')
]

group = ('bit-torrent', _('Download files using BitTorrent applications'))

reserved_usernames = ['debian-deluged']

web_clients = [web_client(name='Deluge', url='/deluge')]


def init():
    """Initialize the Deluge module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-magnet',
                     'deluge:index', short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], name, ports=['http', 'https'],
            is_external=True, is_enabled=is_enabled, enable=enable,
            disable=disable)

        if is_enabled():
            add_shortcut()
            register_group(group)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'deluge', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], name, ports=['http', 'https'],
            is_external=True, is_enabled=is_enabled, enable=enable,
            disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)
    create_group(group[0])


def add_shortcut():
    frontpage.add_shortcut('deluge', name, short_description, url='/deluge',
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.webserver_is_enabled('deluge-plinth') and
            action_utils.service_is_enabled('deluge-web'))


def enable():
    """Enable the module."""
    actions.superuser_run('deluge', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('deluge', ['disable'])
    frontpage.remove_shortcut('deluge')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(8112, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(8112, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/deluge', check_certificate=False))

    return results
