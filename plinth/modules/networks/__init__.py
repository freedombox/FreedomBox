# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to interface with network-manager."""

import subprocess
from logging import Logger

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import daemon, kvstore, menu, network
from plinth.config import DropinConfigs
from plinth.diagnostic_check import DiagnosticCheck
from plinth.package import Packages

from . import privileged

first_boot_steps = [
    {
        'id': 'network_topology_wizard',
        'url': 'networks:network-topology-first-boot',
        'order': 2,
    },
    {
        'id': 'router_setup_wizard',
        'url': 'networks:router-configuration-first-boot',
        'order': 3,
    },
    {
        'id': 'internet_connectivity_type_wizard',
        'url': 'networks:internet-connection-type-first-boot',
        'order': 4,
    },
]

_description = [
    _('Configure network devices. Connect to the Internet via Ethernet, Wi-Fi '
      'or PPPoE. Share that connection with other devices on the network.'),
    _('Devices administered through other methods may not be available for '
      'configuration here.'),
]

logger = Logger(__name__)


class NetworksApp(app_module.App):
    """FreedomBox app for Networks."""

    app_id = 'networks'

    _version = 2

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Networks'),
                               icon='fa-signal', description=_description,
                               manual_page='Networks')
        self.add(info)

        menu_item = menu.Menu('menu-networks', info.name, None, info.icon,
                              'networks:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-networks', ['network-manager', 'batctl'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-networks', [
            '/etc/NetworkManager/dispatcher.d/10-freedombox-batman',
        ])
        self.add(dropin_configs)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()

        interfaces = _get_shared_interfaces()
        addresses = _get_interface_addresses(interfaces)

        for address in addresses:
            results.append(daemon.diagnose_port_listening(53, 'tcp', address))
            results.append(daemon.diagnose_port_listening(53, 'udp', address))

        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        self.enable()


def get_network_topology_type():
    """Return the currently configured network topology type or default."""
    return kvstore.get_default('networks_topology_type', 'to_router')


def set_network_topology_type(network_topology_type):
    """Store the network topology type."""
    kvstore.set('networks_topology_type', network_topology_type)


def get_internet_connection_type():
    """Return the currently configured internet connection type or default."""
    return kvstore.get_default('networks_internet_type', 'unknown')


def set_internet_connection_type(internet_connection_type):
    """Store the internet connection type."""
    return kvstore.set('networks_internet_type', internet_connection_type)


def get_router_configuration_type():
    """Return the currently configured router configuration type or default."""
    return kvstore.get_default('networks_router_configuration_type',
                               'not_configured')


def set_router_configuration_type(router_configuration_type):
    """Store the router configuration type."""
    return kvstore.set('networks_router_configuration_type',
                       router_configuration_type)


def _get_shared_interfaces():
    """Get active network interfaces in shared mode."""
    shared_interfaces = []
    for connection in network.get_connection_list():
        if not connection['is_active']:
            continue

        connection_uuid = connection['uuid']
        connection = network.get_connection(connection_uuid)

        settings_ipv4 = connection.get_setting_ip4_config()
        if settings_ipv4.get_method() == 'shared':
            settings_connection = connection.get_setting_connection()
            interface = settings_connection.get_interface_name()
            if interface:
                shared_interfaces.append(interface)

    return shared_interfaces


def _get_interface_addresses(interfaces):
    """Get the IPv4 addresses for the given interfaces."""
    output = subprocess.check_output(['ip', '-o', 'addr'])
    lines = output.decode().splitlines()

    addresses = []
    for line in lines:
        parts = line.split()
        if parts[1] in interfaces and parts[2] == 'inet':
            addresses.append(parts[3].split('/')[0])

    return addresses
