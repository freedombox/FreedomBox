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

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.i2p.resources import FAVORITES
from plinth.modules.users import register_group

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

service_name = 'i2p'

managed_services = [service_name]

managed_packages = ['i2p']

name = _('I2P')

icon_filename = 'i2p'

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

manual_page = 'I2P'

port_forwarding_info = [
    ('TCP', 4444),
    ('TCP', 4445),
    ('TCP', 6668),
]

tunnels_to_manage = {
    'I2P HTTP Proxy': 'i2p-http-proxy-freedombox',
    'I2P HTTPS Proxy': 'i2p-https-proxy-freedombox',
    'Irc2P': 'i2p-irc-freedombox'
}

app = None


class I2PApp(app_module.App):
    """FreedomBox app for I2P."""

    app_id = 'i2p'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-i2p', name, short_description, 'i2p',
                              'i2p:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-i2p', name, short_description=short_description,
            icon=icon_filename, url='/i2p/', clients=clients, login_required=True,
            allowed_groups=[group[0]])
        self.add(shortcut)

        firewall = Firewall('firewall-i2p-web', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        firewall = Firewall('firewall-i2p-proxies', _('I2P Proxy'),
                            ports=tunnels_to_manage.values(),
                            is_external=False)
        self.add(firewall)

        webserver = Webserver('webserver-i2p', 'i2p-freedombox')
        self.add(webserver)

        daemon = Daemon('daemon-i2p', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the module."""
    global app
    app = I2PApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)

    helper.call('post', app.disable)
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
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(7657, 'tcp6'))
    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/i2p/',
                                         check_certificate=False))

    return results
