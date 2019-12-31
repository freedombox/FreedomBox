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
FreedomBox app to configure OpenVPN server.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 4

managed_services = ['openvpn-server@freedombox']

managed_packages = ['openvpn', 'easy-rsa']

name = _('OpenVPN')

icon_filename = 'openvpn'

short_description = _('Virtual Private Network')

description = [
    format_lazy(
        _('Virtual Private Network (VPN) is a technique for securely '
          'connecting two devices in order to access resources of a '
          'private network.  While you are away from home, you can connect '
          'to your {box_name} in order to join your home network and '
          'access private/internal services provided by {box_name}. '
          'You can also access the rest of the Internet via {box_name} '
          'for added security and anonymity.'), box_name=_(cfg.box_name))
]

manual_page = 'OpenVPN'

port_forwarding_info = [('UDP', 1194)]

app = None

clients = clients


class OpenVPNApp(app_module.App):
    """FreedomBox app for OpenVPN."""

    app_id = 'openvpn'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-openvpn', name, short_description,
                              'openvpn', 'openvpn:index',
                              parent_url_name='apps')
        self.add(menu_item)

        download_profile = \
            format_lazy(_('<a class="btn btn-primary btn-sm" href="{link}">'
                          'Download Profile</a>'),
                        link=reverse_lazy('openvpn:profile'))
        shortcut = frontpage.Shortcut(
            'shortcut-openvpn', name, short_description=short_description,
            icon=icon_filename, description=description + [download_profile],
            configure_url=reverse_lazy('openvpn:index'), login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-openvpn', name, ports=['openvpn'],
                            is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-openvpn', managed_services[0],
                        listen_ports=[(1194, 'udp4')])
        self.add(daemon)


def init():
    """Initialize the OpenVPN module."""
    global app
    app = OpenVPNApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled() \
       and is_setup():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'openvpn', ['upgrade'])
    if app.is_enabled() and is_setup():
        helper.call('post', app.enable)


def is_setup():
    """Return whether the service is running."""
    return actions.superuser_run('openvpn', ['is-setup']).strip() == 'true'
