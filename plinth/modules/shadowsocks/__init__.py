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
FreedomBox app to configure Shadowsocks.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, cfg, frontpage
from plinth.menu import main_menu
from plinth.utils import format_lazy

version = 1

name = _('Shadowsocks')

short_description = _('Socks5 Proxy')

service = None

managed_services = ['shadowsocks-libev-local@freedombox']

managed_packages = ['shadowsocks-libev']

description = [
    _('Shadowsocks is a lightweight and secure SOCKS5 proxy, designed to '
      'protect your Internet traffic. It can be used to bypass Internet '
      'filtering and censorship.'),
    format_lazy(
        _('Your {box_name} can run a Shadowsocks client, that can connect to '
          'a Shadowsocks server. It will also run a SOCKS5 proxy. Local '
          'devices can connect to this proxy, and their data will be '
          'encrypted and proxied through the Shadowsocks server.'), box_name=_(
              cfg.box_name)),
    _('To use Shadowsocks after setup, set the SOCKS5 proxy URL in your '
      'device, browser or application to http://freedombox_address:1080/')
]

manual_page = 'Shadowsocks'


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-send', 'shadowsocks:index',
                     short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service('shadowsocks', name, ports=[
            'shadowsocks-local-plinth'
        ], is_external=False, is_enabled=is_enabled, is_running=is_running,
                                         enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'shadowsocks', ['setup'])
    global service
    if service is None:
        service = service_module.Service('shadowsocks', name, ports=[
            'shadowsocks-local-plinth'
        ], is_external=False, is_enabled=is_enabled, is_running=is_running,
                                         enable=enable, disable=disable)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut(
        'shadowsocks', name, short_description=short_description,
        details=description, configure_url=reverse_lazy('shadowsocks:index'),
        login_required=False)


def is_enabled():
    """Return whether service is enabled."""
    return action_utils.service_is_enabled(managed_services[0])


def is_running():
    """Return whether service is running."""
    return action_utils.service_is_running(managed_services[0])


def enable():
    """Enable service."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable service."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('shadowsocks')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(1080, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(1080, 'tcp6'))

    return results
