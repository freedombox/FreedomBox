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
App component for other apps to use firewall functionality.
"""

import logging

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
        """Returns a list of interfaces in a firewall zone."""
        return firewall.get_interfaces('internal')
