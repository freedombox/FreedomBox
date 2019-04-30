#
# This file is part of FreedomBox.
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
FreedomBox app to configure I2P.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.modules.i2p.resources import FAVORITES
from plinth.modules.users import register_group

from .manifest import backup, clients

version = 1

service_name = 'i2p'

managed_services = [service_name]

managed_packages = ['i2p']

name = _('I2P')

short_description = _('Anonymity Network')

description = [
    _('The Invisible Internet Project is an anonymous network layer intended '
      'to protect communication from censorship and surveillance. I2P '
      'provides anonymity by sending encrypted traffic through a '
      'volunteer-run network distributed around the world.'),
    _('Find more information about I2P on their project '
      '<a href="https://geti2p.net" target="_blank">homepage</a>.'),
    _('The first visit to the provided web interface will initiate the '
      'configuration process.')
]

clients = clients

group = ('i2p', _('Manage I2P application'))

service = None
proxies_service = None

manual_page = 'I2P'

tunnels_to_manage = {
    'I2P HTTP Proxy': 'i2p-http-proxy-freedombox',
    'I2P HTTPS Proxy': 'i2p-https-proxy-freedombox',
    'Irc2P': 'i2p-irc-freedombox'
}


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'i2p', 'i2p:index', short_description)
    register_group(group)

    global service, proxies_service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)
        proxies_service = service_module.Service(
            'i2p-proxies', name, ports=tunnels_to_manage.values(),
            is_external=False, is_enabled=is_enabled, is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)

    helper.call('post', disable)
    # Add favorites to the configuration
    for fav in FAVORITES:
        args = [
            'add-favorite',
            '--name',
            fav.get('name'),
            '--url',
            fav.get('url'),
        ]
        if 'icon' in fav:
            args.extend(['--icon', fav.get('icon')])

        if 'description' in fav:
            args.extend(['--description', fav.get('description')])

        helper.call('post', actions.superuser_run, 'i2p', args)


    # Tunnels to all interfaces
    for tunnel in tunnels_to_manage:
        helper.call('post', actions.superuser_run, 'i2p', [
            'set-tunnel-property', '--name', tunnel, '--property', 'interface',
            '--value', '0.0.0.0'
        ])
    helper.call('post', enable)
    global service, proxies_service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)
        proxies_service = service_module.Service(
            'i2p-proxies', name, ports=tunnels_to_manage.values(),
            is_external=False, is_enabled=is_enabled, is_running=is_running)

    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', proxies_service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut('i2p', name, short_description=short_description,
                           url='/i2p/', login_required=True,
                           allowed_groups=[group[0]])


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('i2p')


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('i2p') and \
        action_utils.webserver_is_enabled('i2p-freedombox')


def enable():
    """Enable the module."""
    actions.superuser_run('i2p', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('i2p', ['disable'])
    frontpage.remove_shortcut('i2p')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(7657, 'tcp6'))
    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/i2p/',
                                         check_certificate=False))

    return results
