# SPDX-License-Identifier: AGPL-3.0-or-later
"""
App component for other apps to use firewall functionality.
"""

import logging
import re

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app
from plinth.modules import firewall

logger = logging.getLogger(__name__)


class Firewall(app.FollowerComponent):
    """Component to open/close firewall ports for an app."""

    _all_firewall_components = {}

    def __init__(self, component_id, name=None, ports=None, is_external=False):
        """Initialize the firewall component."""
        super().__init__(component_id)

        if not ports:
            ports = []

        self.name = name
        self.ports = ports
        self.is_external = is_external

        self._all_firewall_components[component_id] = self

    @property
    def ports_details(self):
        """Retrieve details of ports associated with this component.."""
        ports_details = []
        for port in self.ports:
            ports_details.append({
                'name': port,
                'details': firewall.get_port_details(port),
            })

        return ports_details

    @classmethod
    def list(cls):
        """Return a list of all firewall ports."""
        return cls._all_firewall_components.values()

    def enable(self):
        """Open firewall ports when the component is enabled."""
        super().enable()
        firewall.try_with_reload(self._enable)

    def _enable(self):
        """Open firewall ports."""
        internal_enabled_ports = firewall.get_enabled_services(zone='internal')
        external_enabled_ports = firewall.get_enabled_services(zone='external')

        logger.info('Firewall ports opened - %s, %s', self.name, self.ports)
        for port in self.ports:
            if port not in internal_enabled_ports:
                firewall.add_service(port, zone='internal')

            if (self.is_external and port not in external_enabled_ports):
                firewall.add_service(port, zone='external')

    def disable(self):
        """Close firewall ports when the component is disabled."""
        super().disable()
        firewall.try_with_reload(self._disable)

    def _disable(self):
        """Close firewall ports."""
        internal_enabled_ports = firewall.get_enabled_services(zone='internal')
        external_enabled_ports = firewall.get_enabled_services(zone='external')

        logger.info('Firewall ports closed - %s, %s', self.name, self.ports)
        for port in self.ports:
            if port in internal_enabled_ports:
                enabled_components_on_port = [
                    component.is_enabled()
                    for component in self._all_firewall_components.values()
                    if port in component.ports
                    and self.component_id != component.component_id
                ]
                if not any(enabled_components_on_port):
                    firewall.remove_service(port, zone='internal')

            if port in external_enabled_ports:
                enabled_components_on_port = [
                    component.is_enabled()
                    for component in self._all_firewall_components.values()
                    if port in component.ports and self.component_id !=
                    component.component_id and component.is_external
                ]
                if not any(enabled_components_on_port):
                    firewall.remove_service(port, zone='external')

    @staticmethod
    def get_internal_interfaces():
        """Returns a list of interfaces in a firewall zone.

        Filter out tun interfaces as they are always assumed to be internal
        interfaces.

        """
        return [
            interface for interface in firewall.get_interfaces('internal')
            if not re.fullmatch(r'tun\d+', interface)
        ]

    def diagnose(self):
        """Check if the firewall ports are open and only as expected.

        See :py:meth:`plinth.app.Component.diagnose`.

        """
        results = []
        internal_ports = firewall.get_enabled_services(zone='internal')
        external_ports = firewall.get_enabled_services(zone='external')
        for port_detail in self.ports_details:
            port = port_detail['name']
            details = ', '.join(
                (f'{port_number}/{protocol}'
                 for port_number, protocol in port_detail['details']))

            # Internal zone
            result = 'passed' if port in internal_ports else 'failed'
            template = _(
                'Port {name} ({details}) available for internal networks')
            testname = format_lazy(template, name=port, details=details)
            results.append([testname, result])

            # External zone
            if self.is_external:
                result = 'passed' if port in external_ports else 'failed'
                template = _(
                    'Port {name} ({details}) available for external networks')
                testname = format_lazy(template, name=port, details=details)
            else:
                result = 'passed' if port not in external_ports else 'failed'
                template = _(
                    'Port {name} ({details}) unavailable for external networks'
                )
                testname = format_lazy(template, name=port, details=details)
            results.append([testname, result])

        return results


def get_port_forwarding_info(app_):
    """Return a list of ports to be forwarded for this app to work."""
    from plinth.modules import networks
    info = {
        'network_topology_type': networks.get_network_topology_type(),
        'router_configuration_type': networks.get_router_configuration_type(),
        'ports': []
    }
    for component in app_.components.values():
        if not isinstance(component, Firewall):
            continue

        if not component.is_external:
            continue

        for port in component.ports_details:
            if port['name'] in ['http', 'https']:
                continue

            for detail in port['details']:
                info['ports'].append({
                    'name': port['name'],
                    'protocol': detail[1].upper(),
                    'ports': detail[0]
                })

    return info
