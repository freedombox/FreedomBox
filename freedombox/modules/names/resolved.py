# SPDX-License-Identifier: AGPL-3.0-or-later
"""Module to interact with systemd-resolved over DBus."""

import ipaddress
import json
import subprocess

from django.utils.translation import gettext_lazy as _

from plinth.utils import import_from_gi

gio = import_from_gi('Gio', '2.0')

RESOLVE_NAME = 'org.freedesktop.resolve1'
RESOLVE_PATH = '/org/freedesktop/resolve1'
MANAGER_INTERFACE = 'org.freedesktop.resolve1.Manager'
LINK_INTERFACE = 'org.freedesktop.resolve1.Link'


class DNSServer:
    """Representation of a DNS server in systemd-resolved state."""

    def __init__(self, link_index: int, address_class: int,
                 address_ints: list[int], port: int = 0,
                 domain_name: str | None = None):
        self.link_index = link_index
        self.address_class = address_class
        self.address = ipaddress.ip_address(bytes(address_ints))
        self.port = port
        self.domain_name = domain_name

    def __str__(self):
        if self.port:
            if self.address.version == 4:  # IPv4
                address_str = f'{self.address.compressed}:{self.port}'
            else:  # IPv6
                address_str = f'[{self.address.compressed}]:{self.port}'
        else:
            address_str = self.address.compressed

        if self.domain_name:
            return f'{address_str} ({self.domain_name})'

        return address_str


class Link:
    """systemd-resolved state for a particular link or global context."""

    def __init__(self, connection, object_path, link_index: int = 0,
                 interface_name: str | None = None):
        """Fetch all the relevant properties for a link over DBus."""
        if not link_index:  # Global
            interface = MANAGER_INTERFACE
        else:
            interface = LINK_INTERFACE

        self.proxy = gio.DBusProxy.new_sync(connection,
                                            gio.DBusProxyFlags.NONE, None,
                                            RESOLVE_NAME, object_path,
                                            interface)

        self.link_index = link_index
        self.interface_name = interface_name

        self.dns_over_tls = self.proxy.get_cached_property(
            'DNSOverTLS').unpack()
        self.dnssec = self.proxy.get_cached_property('DNSSEC').unpack()
        self.dnssec_supported = self.proxy.get_cached_property(
            'DNSSECSupported')

        self.dns_servers = self._new_dns_servers(
            self.proxy.get_cached_property('DNSEx'))

        self.fallback_dns_servers = None
        if not link_index:
            self.fallback_dns_servers = self._new_dns_servers(
                self.proxy.get_cached_property('FallbackDNSEx'))

        self.current_dns_server = self._new_dns_server(
            self.proxy.get_cached_property('CurrentDNSServerEx'))

    def get_link(self, link_index):
        """Return a string path to a link's DBus object."""
        return self.proxy.GetLink('(i)', link_index)

    @property
    def dns_over_tls_string(self):
        """Return a string representation for DNS-over-TLS status."""
        value_map = {
            'yes': _('yes'),
            'opportunistic': _('opportunistic'),
            'no': _('no')
        }
        return value_map.get(self.dns_over_tls, self.dns_over_tls)

    @property
    def dnssec_string(self):
        """Return a string representation for DNSSEC status."""
        value_map = {
            'yes': _('yes'),
            'allow-downgrade': _('allow-downgrade'),
            'no': _('no')
        }
        return value_map.get(self.dnssec, self.dnssec)

    @property
    def dnssec_supported_string(self):
        """Return a string representation for whether DNSSEC is supported."""
        return _('supported') if self.dnssec_supported else _('unsupported')

    def _new_dns_servers(self, dns_tuples):
        """Return list of DNS Server objects from variant tuple.

        Global DNS servers list also contains individual link DNS servers.
        Ignore those.
        """
        return [
            self._new_dns_server(dns_tuple) for dns_tuple in dns_tuples
            if self.link_index != 0 or dns_tuple[0] == 0
        ]

    def _new_dns_server(self, dns_tuple):
        """Return a DNS Server object from variant tuple.

        Tuple can be prefixed by link index in case of DNS server for global
        context. Handle both cases. Entire tuple may be empty. Return None in
        that case.
        """
        if self.link_index:  # Not global
            dns_tuple = (self.link_index, ) + tuple(dns_tuple)

        if not dns_tuple[2]:  # Empty address
            return None

        return DNSServer(*dns_tuple)

    def __str__(self):
        dnssec_supported = ('supported'
                            if self.dnssec_supported else 'unspported')
        value = ''
        if not self.link_index:
            value += 'Global\n'
        else:
            value = f'Link {self.link_index} ({self.interface_name})\n'

        if self.current_dns_server:
            value += f'  Current DNS Server: {str(self.current_dns_server)}\n'

        if self.dns_servers:
            value += '  DNS Servers:\n'
            for server in self.dns_servers:
                value += f'    {server}\n'

        if self.fallback_dns_servers:
            value += '  Fallback DNS Servers: \n'
            for server in self.fallback_dns_servers:
                value += f'    {server}\n'

        value += f'  DNS-over-TLS: {self.dns_over_tls}\n'
        value += f'  DNSSEC: {self.dnssec}/{dnssec_supported}\n'
        return value


def get_links():
    """Return the list of network interfaces and their indices."""
    process = subprocess.run(['ip', '--json', 'link'], stdout=subprocess.PIPE,
                             check=True)
    output = json.loads(process.stdout.decode())

    links = {}  # Maintain link index order
    for entry in output:
        links[entry['ifindex']] = entry['ifname']

    return links


def get_status():
    """Return the current status of systemd-resolved daemon."""
    link_status = []
    connection = gio.bus_get_sync(gio.BusType.SYSTEM)
    global_link = Link(connection, RESOLVE_PATH)
    link_status.append(global_link)

    links = get_links()
    for link_index, interface_name in links.items():
        if interface_name == 'lo':
            continue

        link_path = global_link.get_link(link_index)
        link_status.append(
            Link(connection, link_path, link_index, interface_name))

    return link_status
