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

from django.contrib.auth.decorators import login_required
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from plinth import actions
from plinth import cfg
from plinth import package
from plinth.signals import service_enabled
import plinth.service as service_module


LOGGER = logging.getLogger(__name__)


def init():
    """Initailze firewall module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Firewall'), 'glyphicon-fire', 'firewall:index', 50)

    service_enabled.connect(on_service_enabled)


@login_required
@package.required(['firewalld'])
def index(request):
    """Serve introcution page"""
    if not get_enabled_status():
        return TemplateResponse(request, 'firewall.html',
                                {'title': _('Firewall'),
                                 'firewall_status': 'not_running'})

    internal_enabled_services = get_enabled_services(zone='internal')
    external_enabled_services = get_enabled_services(zone='external')

    return TemplateResponse(
        request, 'firewall.html',
        {'title': _('Firewall'),
         'services': list(service_module.SERVICES.values()),
         'internal_enabled_services': internal_enabled_services,
         'external_enabled_services': external_enabled_services})


def get_enabled_status():
    """Return whether firewall is enabled"""
    output = _run(['get-status'], superuser=True)
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
    service = service_module.SERVICES[service_id]
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
                    for service_ in service_module.SERVICES.values()
                    if port in service_.ports and
                    service_id != service_.service_id]
                if not any(enabled_services_on_port):
                    remove_service(port, zone='internal')

            if port in external_enabled_services:
                enabled_services_on_port = [
                    service_.is_enabled()
                    for service_ in service_module.SERVICES.values()
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
