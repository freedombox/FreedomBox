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
Plinth module to configure a firewall
"""

from django.utils.translation import ugettext_lazy as _
import logging

from plinth import actions
from plinth import cfg
from plinth.menu import main_menu
from plinth.signals import service_enabled
import plinth.service as service_module
from plinth.utils import format_lazy


version = 1

is_essential = True

managed_packages = ['firewalld']

title = _('Firewall')

description = [
    format_lazy(
        _('Firewall is a security system that controls the incoming and '
          'outgoing network traffic on your {box_name}. Keeping a '
          'firewall enabled and properly configured reduces risk of '
          'security threat from the Internet.'), box_name=cfg.box_name)
]

LOGGER = logging.getLogger(__name__)


def init():
    """Initailze firewall module"""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-fire', 'firewall:index')

    service_enabled.connect(on_service_enabled)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)


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


def add_service(port, zone):
    """Enable a service in firewall"""
    _run(['add-service', port, '--zone', zone], superuser=True)


def remove_service(port, zone):
    """Remove a service in firewall"""
    _run(['remove-service', port, '--zone', zone], superuser=True)


def on_service_enabled(sender, service_id, enabled, **kwargs):
    """
    Enable/disable firewall ports when a service is
    enabled/disabled.
    """
    del sender  # Unused
    del kwargs  # Unused

    internal_enabled_services = get_enabled_services(zone='internal')
    external_enabled_services = get_enabled_services(zone='external')

    LOGGER.info('Service enabled - %s, %s', service_id, enabled)
    service = service_module.services[service_id]
    for port in service.ports:
        if enabled:
            if port not in internal_enabled_services:
                add_service(port, zone='internal')

            if (service.is_external and
                    port not in external_enabled_services):
                add_service(port, zone='external')
            else:
                # service already configured.
                pass
        else:
            if port in internal_enabled_services:
                enabled_services_on_port = [
                    service_.is_enabled()
                    for service_ in service_module.services.values()
                    if port in service_.ports and
                    service_id != service_.service_id]
                if not any(enabled_services_on_port):
                    remove_service(port, zone='internal')

            if port in external_enabled_services:
                enabled_services_on_port = [
                    service_.is_enabled()
                    for service_ in service_module.services.values()
                    if port in service_.ports and
                    service_id != service_.service_id and
                    service_.is_external]
                if not any(enabled_services_on_port):
                    remove_service(port, zone='external')


def _run(arguments, superuser=False):
    """Run an given command and raise exception if there was an error"""
    command = 'firewall'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
