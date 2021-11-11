# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to interface with network-manager.
"""

import subprocess
from logging import Logger

from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import daemon, kvstore, menu, network
from plinth.package import Packages

version = 1

is_essential = True

managed_packages = ['network-manager', 'batctl']

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

app = None


class NetworksApp(app_module.App):
    """FreedomBox app for Networks."""

    app_id = 'networks'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, name=_('Networks'),
                               icon='fa-signal', description=_description,
                               manual_page='Networks')
        self.add(info)

        menu_item = menu.Menu('menu-networks', info.name, None, info.icon,
                              'networks:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-networks', managed_packages)
        self.add(packages)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()

        interfaces = _get_shared_interfaces()
        addresses = _get_interface_addresses(interfaces)

        for address in addresses:
            results.append(daemon.diagnose_port_listening(53, 'tcp', address))
            results.append(daemon.diagnose_port_listening(53, 'udp', address))

        results.append(_diagnose_dnssec('4'))
        results.append(_diagnose_dnssec('6'))

        return results


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    actions.superuser_run('networks')
    helper.call('post', app.enable)


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


def _diagnose_dnssec(kind='4'):
    """Perform diagnostic on whether the system is using DNSSEC.

    Kind is either '4' or '6' for IPv4 and IPv6 respectively.
    """
    kind_option = {'4': '-4', '6': '-6'}[kind]

    result = 'failed'
    try:
        output = subprocess.check_output([
            'dig', kind_option, '+time=2', '+tries=1',
            'test.dnssec-or-not.net', 'TXT'
        ])

        if 'Yes, you are using DNSSEC' in output.decode():
            result = 'passed'
    except subprocess.CalledProcessError:
        pass

    template = _('Using DNSSEC on IPv{kind}')
    testname = format_lazy(template, kind=kind)

    return [testname, result]
