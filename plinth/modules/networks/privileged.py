# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure network manager.

During initial setup, configure networking for all wired and wireless devices
by creating network manager connections.
"""

import collections
import itertools
import logging
import re
import subprocess

from plinth import action_utils
from plinth.actions import privileged


def _sort_interfaces(interfaces: list[str]) -> list[str]:
    """Sort interfaces in a well-defined way: eth0, eth1, eth2, ... eth10."""

    def key_func(interface):
        parts = re.findall(r'(\D*)(\d*)', interface)
        parts = [(string, int(number) if number else number)
                 for string, number in parts]
        return list(itertools.chain(parts))

    return sorted(interfaces, key=key_func)


def _get_interfaces() -> dict[str, list[str]]:
    """Return all network interfaces by their type."""
    output = subprocess.check_output(
        ['nmcli', '--terse', '--fields', 'type,device', 'device'])
    interfaces = collections.defaultdict(list)
    for line in output.decode().splitlines():
        type_, _, interface = line.partition(':')
        interfaces[type_].append(interface)

    for type_ in interfaces:
        interfaces[type_] = _sort_interfaces(interfaces[type_])

    return interfaces


def _add_connection(connection_name: str, interface: str,
                    remaining_arguments: list[str]):
    """Add an Ethernet/Wi-Fi connection of type regular or shared."""
    output = subprocess.check_output(
        ['nmcli', '--terse', '--fields', 'name,device', 'con', 'show'])
    lines = output.decode().splitlines()
    if f'{connection_name}:{interface}' in lines:
        logging.info('Connection %s already exists for device %s, not adding.',
                     connection_name, interface)
    else:
        action_utils.run([
            'nmcli', 'con', 'add', 'con-name', connection_name, 'ifname',
            interface
        ] + remaining_arguments, check=True)


def _activate_connection(connection_name: str):
    """Activate a network connection in a background process."""
    subprocess.Popen(['nohup', 'nmcli', 'con', 'up', connection_name],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _configure_regular_interface(interface: str, zone: str):
    """Create a connection that is not a shared connection."""
    connection_name = 'FreedomBox WAN'
    properties = {'connection.autoconnect': 'TRUE', 'connection.zone': zone}

    # Create n-m connection for a regular interface
    _add_connection(connection_name, interface, ['type', 'ethernet'])
    _set_connection_properties(connection_name, properties)
    _activate_connection(connection_name)

    logging.info('Configured interface %s for %s use as %s.', interface, zone,
                 connection_name)


def _configure_shared_interface(interface: str):
    """Create a shared connection that has traffic forwarding enabled.

    Shared connection means:
    - Self-assign an address and network
    - Start and manage DNS server (dnsmasq)
    - Start and manage DHCP server (dnsmasq)
    - Register address with mDNS
    - Add firewall rules for NATing from this interface
    """
    connection_name = f'FreedomBox LAN {interface}'
    properties = {
        'connection.autoconnect': 'TRUE',
        'connection.zone': 'internal',
        'ipv4.method': 'shared'
    }

    # Create n-m connection for eth1
    _add_connection(connection_name, interface, ['type', 'ethernet'])
    _set_connection_properties(connection_name, properties)
    _activate_connection(connection_name)

    logging.info('Configured interface %s for shared use as %s.', interface,
                 connection_name)


def _set_connection_properties(connection_name: str, properties: dict[str,
                                                                      str]):
    """Configure property key/values on a connection."""
    for key, value in properties.items():
        action_utils.run(
            ['nmcli', 'con', 'modify', connection_name, key, value],
            check=True)


def _configure_wireless_interface(interface: str):
    """Configure a wireless access point."""
    connection_name = f'FreedomBox {interface}'
    ssid = f'FreedomBox{interface}'
    secret = 'freedombox123'
    properties = {
        'connection.autoconnect': 'TRUE',
        'connection.zone': 'internal',
        'ipv4.method': 'shared',
        'wifi.mode': 'ap',
        'wifi-sec.key-mgmt': 'wpa-psk',
        'wifi-sec.psk': secret
    }

    _add_connection(connection_name, interface, ['type', 'wifi', 'ssid', ssid])
    _set_connection_properties(connection_name, properties)
    _activate_connection(connection_name)

    logging.info('Configured interface %s for shared use as %s', interface,
                 connection_name)


def _multi_wired_setup(interfaces: list[str]):
    """Configure all Ethernet connections on a system with many of them."""
    _configure_regular_interface(interfaces[0], 'external')

    for interface in interfaces[1:]:
        _configure_shared_interface(interface)


def _one_wired_setup(interface: str, interfaces: dict[str, list[str]]):
    """Configure an Ethernet connection on a system with only one."""
    if not len(interfaces['wifi']):
        _configure_regular_interface(interface, 'internal')
    else:
        _configure_regular_interface(interface, 'external')


def _wireless_setup(interfaces: list[str]):
    """Configure all wireless access points."""
    for interface in interfaces:
        _configure_wireless_interface(interface)


@privileged
def setup():
    """Create network manager connections.

    For a user who installed using freedombox-setup Debian package, when
    FreedomBox Service (Plinth) is run for the first time, don't run network
    setup. This is ensured by checking for the file
    /var/lib/freedombox/is-freedombox-disk-image which will not exist.

    For a user who installed using FreedomBox disk image, when FreedomBox
    Service (Plinth) runs for the first time, setup process executes and
    triggers the script due networks module being an essential module.
    """
    if not action_utils.is_disk_image():
        logging.info(
            'Not a FreedomBox disk image. Skipping network configuration.')
        return

    logging.info('Setting up network configuration...')
    interfaces = _get_interfaces()

    if len(interfaces['ethernet']) == 0:
        logging.info('No wired interfaces detected.')
    elif len(interfaces['ethernet']) == 1:
        _one_wired_setup(interfaces['ethernet'][0], interfaces)
    else:
        _multi_wired_setup(interfaces['ethernet'])

    _wireless_setup(interfaces['wifi'])

    logging.info('Done setting up network configuration.')
