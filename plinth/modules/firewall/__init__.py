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
FreedomBox app to configure a firewall.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.utils import Version, format_lazy

from .manifest import backup  # noqa, pylint: disable=unused-import

version = 2

is_essential = True

managed_packages = ['firewalld', 'nftables']

managed_services = ['firewalld']

name = _('Firewall')

description = [
    format_lazy(
        _('Firewall is a security system that controls the incoming and '
          'outgoing network traffic on your {box_name}. Keeping a '
          'firewall enabled and properly configured reduces risk of '
          'security threat from the Internet.'), box_name=cfg.box_name)
]

manual_page = 'Firewall'

_port_details = {}

app = None


class FirewallApp(app_module.App):
    """FreedomBox app for Firewall."""

    app_id = 'firewall'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-firewall', name, None, 'fa-shield',
                              'firewall:index', parent_url_name='system')
        self.add(menu_item)

        daemon = Daemon('daemon-firewall', managed_services[0])
        self.add(daemon)


def init():
    """Initailze firewall module"""
    global app
    app = FirewallApp()
    app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    _run(['setup'], superuser=True)


def force_upgrade(helper, packages):
    """Force upgrade firewalld to resolve conffile prompts."""
    if 'firewalld' not in packages:
        return False

    # firewalld 0.6.x -> 0.7.x, 0.6.x -> 0.8.x, 0.7.x -> 0.8.x
    package = packages['firewalld']
    if Version(package['current_version']) >= Version('0.8') or \
       Version(package['new_version']) < Version('0.7'):
        return False

    helper.install(['firewalld'], force_configuration='new')
    _run(['setup'], superuser=True)
    return True


def get_enabled_status():
    """Return whether firewall is enabled"""
    output = _run(['get-status'], superuser=True)
    if not output:
        return False
    else:
        return output.split()[0] == 'running'


def get_enabled_services(zone):
    """Return the status of various services currently enabled"""
    output = _run(['get-enabled-services', '--zone', zone], superuser=True)
    return output.split()


def get_port_details(service_port):
    """Return the port types and numbers for a service port"""
    try:
        return _port_details[service_port]
    except KeyError:
        output = _run(['get-service-ports', '--service', service_port],
                      superuser=True)
        _port_details[service_port] = output.strip()
        return _port_details[service_port]


def get_interfaces(zone):
    """Return the list of interfaces in a zone."""
    output = _run(['get-interfaces', '--zone', zone], superuser=True)
    return output.split()


def add_service(port, zone):
    """Enable a service in firewall"""
    _run(['add-service', port, '--zone', zone], superuser=True)


def remove_service(port, zone):
    """Remove a service in firewall"""
    _run(['remove-service', port, '--zone', zone], superuser=True)


def _run(arguments, superuser=False):
    """Run an given command and raise exception if there was an error"""
    command = 'firewall'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
