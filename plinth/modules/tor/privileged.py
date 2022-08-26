# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Tor service."""

import codecs
import os
import re
import socket
import subprocess
import time
from typing import Any, Optional, Union

import augeas

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.tor.utils import (APT_TOR_PREFIX, get_augeas,
                                      get_real_apt_uri_path, iter_apt_uris)

SERVICE_FILE = '/etc/firewalld/services/tor-{0}.xml'
TOR_CONFIG = '/files/etc/tor/instances/plinth/torrc'
TOR_STATE_FILE = '/var/lib/tor-instances/plinth/state'
TOR_AUTH_COOKIE = '/var/run/tor-instances/plinth/control.authcookie'


@privileged
def setup(old_version: int):
    """Setup Tor configuration after installing it."""
    if old_version and old_version <= 4:
        _upgrade_orport_value()
        return

    _first_time_setup()


def _first_time_setup():
    """Setup Tor configuration for the first time setting defaults."""
    # Disable default tor service. We will use tor@plinth instance
    # instead.
    _disable_apt_transport_tor()
    action_utils.service_disable('tor')

    subprocess.run(['tor-instance-create', 'plinth'], check=True)

    # Remove line starting with +SocksPort, since our augeas lens
    # doesn't handle it correctly.
    with open('/etc/tor/instances/plinth/torrc', 'r',
              encoding='utf-8') as torrc:
        torrc_lines = torrc.readlines()
    with open('/etc/tor/instances/plinth/torrc', 'w',
              encoding='utf-8') as torrc:
        for line in torrc_lines:
            if not line.startswith('+'):
                torrc.write(line)

    aug = augeas_load()

    aug.set(TOR_CONFIG + '/SocksPort[1]', '[::]:9050')
    aug.set(TOR_CONFIG + '/SocksPort[2]', '0.0.0.0:9050')
    aug.set(TOR_CONFIG + '/ControlPort', '9051')
    _enable_relay(relay=True, bridge=True, aug=aug)
    aug.set(TOR_CONFIG + '/ExitPolicy[1]', 'reject *:*')
    aug.set(TOR_CONFIG + '/ExitPolicy[2]', 'reject6 *:*')

    aug.set(TOR_CONFIG + '/VirtualAddrNetworkIPv4', '10.192.0.0/10')
    aug.set(TOR_CONFIG + '/AutomapHostsOnResolve', '1')
    aug.set(TOR_CONFIG + '/TransPort[1]', '127.0.0.1:9040')
    aug.set(TOR_CONFIG + '/TransPort[2]', '[::1]:9040')
    aug.set(TOR_CONFIG + '/DNSPort[1]', '127.0.0.1:9053')
    aug.set(TOR_CONFIG + '/DNSPort[2]', '[::1]:9053')

    aug.set(TOR_CONFIG + '/HiddenServiceDir',
            '/var/lib/tor-instances/plinth/hidden_service')
    aug.set(TOR_CONFIG + '/HiddenServicePort[1]', '22 127.0.0.1:22')
    aug.set(TOR_CONFIG + '/HiddenServicePort[2]', '80 127.0.0.1:80')
    aug.set(TOR_CONFIG + '/HiddenServicePort[3]', '443 127.0.0.1:443')

    aug.save()

    action_utils.service_enable('tor@plinth')
    action_utils.service_restart('tor@plinth')
    _update_ports()

    # wait until hidden service information is available
    tries = 0
    while not _get_hidden_service()['enabled']:
        tries += 1
        if tries >= 12:
            return

        time.sleep(10)


def _upgrade_orport_value():
    """Change ORPort value from auto to 9001.

    When ORPort is set to 'auto', Tor automatically allocates a port for it.
    During it's first run, we able to extract the port number and open the
    firewall port. However, unlike for pluggable transports, Tor does not seem
    to store this port for future reuse in the state file. It hence opens a new
    port every time it is started. This leads to a new port being assigned on
    next Tor startup and leads to relay functionality not being reachable from
    outside.

    According to the documentation, only possible values for ORPort are a fixed
    number or 0 (disable) or auto (above behavior). Choose 9001 as this is
    the commonly used port number for ORPort. The recommended port number of
    443 is not possible in FreedomBox due it is use for other purposes.

    """
    aug = augeas_load()

    if _is_relay_enabled(aug):
        aug.set(TOR_CONFIG + '/ORPort[1]', '9001')
        aug.set(TOR_CONFIG + '/ORPort[2]', '[::]:9001')

    aug.save()

    action_utils.service_try_restart('tor@plinth')

    # Tor may not be running, don't try to read/update all ports
    _update_port('orport', 9001)
    action_utils.service_restart('firewalld')


@privileged
def configure(use_upstream_bridges: Optional[bool] = None,
              upstream_bridges: Optional[str] = None,
              relay: Optional[bool] = None,
              bridge_relay: Optional[bool] = None,
              hidden_service: Optional[bool] = None,
              apt_transport_tor: Optional[bool] = None):
    """Configure Tor."""
    aug = augeas_load()

    _use_upstream_bridges(use_upstream_bridges, aug=aug)

    if use_upstream_bridges:
        relay = False
        bridge_relay = False

    if upstream_bridges:
        _set_upstream_bridges(upstream_bridges, aug=aug)

    _enable_relay(relay, bridge_relay, aug=aug)

    if hidden_service:
        _enable_hs(aug=aug)
    elif hidden_service is not None:
        _disable_hs(aug=aug)

    if apt_transport_tor:
        _enable_apt_transport_tor()
    elif apt_transport_tor is not None:
        _disable_apt_transport_tor()


@privileged
def update_ports():
    """Update firewall ports based on what Tor uses."""
    _update_ports()


@privileged
def restart():
    """Restart Tor."""
    if (action_utils.service_is_enabled('tor@plinth', strict_check=True)
            and action_utils.service_is_running('tor@plinth')):
        action_utils.service_restart('tor@plinth')

        aug = augeas_load()
        if aug.get(TOR_CONFIG + '/HiddenServiceDir'):
            # wait until hidden service information is available
            tries = 0
            while not _get_hidden_service()['enabled']:
                tries += 1
                if tries >= 12:
                    return
                time.sleep(10)


@privileged
def get_status() -> dict[str, Union[bool, str, dict[str, Any]]]:
    """Return dict with Tor status."""
    aug = augeas_load()
    return {
        'use_upstream_bridges': _are_upstream_bridges_enabled(aug),
        'upstream_bridges': _get_upstream_bridges(aug),
        'relay_enabled': _is_relay_enabled(aug),
        'bridge_relay_enabled': _is_bridge_relay_enabled(aug),
        'ports': _get_ports(),
        'hidden_service': _get_hidden_service(aug)
    }


def _are_upstream_bridges_enabled(aug) -> bool:
    """Return whether upstream bridges are being used."""
    use_bridges = aug.get(TOR_CONFIG + '/UseBridges')
    return use_bridges == '1'


def _get_upstream_bridges(aug) -> str:
    """Return upstream bridges separated by newlines."""
    matches = aug.match(TOR_CONFIG + '/Bridge')
    bridges = [aug.get(match) for match in matches]
    return '\n'.join(bridges)


def _is_relay_enabled(aug) -> bool:
    """Return whether a relay is enabled."""
    orport = aug.get(TOR_CONFIG + '/ORPort[1]')
    return bool(orport) and orport != '0'


def _is_bridge_relay_enabled(aug) -> bool:
    """Return whether bridge relay is enabled."""
    bridge = aug.get(TOR_CONFIG + '/BridgeRelay')
    return bridge == '1'


def _get_ports() -> dict[str, str]:
    """Return dict mapping port names to numbers."""
    ports = {}
    try:
        ports['orport'] = _get_orport()
    except Exception:
        pass

    try:
        with open(TOR_STATE_FILE, 'r', encoding='utf-8') as state_file:
            for line in state_file:
                matches = re.match(
                    r'^\s*TransportProxy\s+(\S*)\s+\S+:(\d+)\s*$', line)
                if matches:
                    ports[matches.group(1)] = matches.group(2)
    except FileNotFoundError:
        pass

    return ports


def _get_orport() -> str:
    """Return the ORPort by querying running instance."""
    cookie = open(TOR_AUTH_COOKIE, 'rb').read()
    cookie = codecs.encode(cookie, 'hex').decode()

    commands = '''AUTHENTICATE {cookie}
GETINFO net/listeners/or
QUIT
'''.format(cookie=cookie)

    tor_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tor_socket.connect(('localhost', 9051))
    tor_socket.send(commands.encode())
    response = tor_socket.recv(1024)
    tor_socket.close()

    line = response.split(b'\r\n')[1].decode()
    matches = re.match(r'.*=".+:(\d+)"', line)
    return matches.group(1)


def _get_hidden_service(aug=None) -> dict[str, Any]:
    """Return a string with configured Tor hidden service information."""
    hs_enabled = False
    hs_status = 'Ok'
    hs_hostname = None
    hs_ports = []

    if not aug:
        aug = augeas_load()

    hs_dir = aug.get(TOR_CONFIG + '/HiddenServiceDir')
    hs_port_paths = aug.match(TOR_CONFIG + '/HiddenServicePort')

    for hs_port_path in hs_port_paths:
        port_info = aug.get(hs_port_path).split()
        hs_ports.append({'virtport': port_info[0], 'target': port_info[1]})

    if not hs_dir:
        hs_status = 'Not Configured'
    else:
        try:
            with open(os.path.join(hs_dir, 'hostname'), 'r',
                      encoding='utf-8') as conf_file:
                hs_hostname = conf_file.read().strip()
                hs_enabled = True
        except Exception:
            hs_status = 'Not available (Run Tor at least once)'

    return {
        'enabled': hs_enabled,
        'status': hs_status,
        'hostname': hs_hostname,
        'ports': hs_ports
    }


def _enable():
    """Enable and start the service."""
    action_utils.service_enable('tor@plinth')
    _update_ports()


def _disable():
    """Disable and stop the service."""
    _disable_apt_transport_tor()
    action_utils.service_disable('tor@plinth')


def _use_upstream_bridges(use_upstream_bridges: Optional[bool] = None,
                          aug=None):
    """Enable use of upstream bridges."""
    if use_upstream_bridges is None:
        return

    if not aug:
        aug = augeas_load()

    if use_upstream_bridges:
        aug.set(TOR_CONFIG + '/UseBridges', '1')
    else:
        aug.set(TOR_CONFIG + '/UseBridges', '0')

    aug.save()


def _set_upstream_bridges(upstream_bridges=None, aug=None):
    """Set list of upstream bridges."""
    if upstream_bridges is None:
        return

    if not aug:
        aug = augeas_load()

    aug.remove(TOR_CONFIG + '/Bridge')
    if upstream_bridges:
        bridges = [bridge.strip() for bridge in upstream_bridges.split('\n')]
        bridges = [bridge for bridge in bridges if bridge]
        for bridge in bridges:
            parts = [part for part in bridge.split() if part]
            bridge = ' '.join(parts)
            aug.set(TOR_CONFIG + '/Bridge[last() + 1]', bridge.strip())

    aug.set(TOR_CONFIG + '/ClientTransportPlugin',
            'obfs3,scramblesuit,obfs4 exec /usr/bin/obfs4proxy')

    aug.save()


def _enable_relay(relay: Optional[bool], bridge: Optional[bool],
                  aug: augeas.Augeas):
    """Enable Tor bridge relay."""
    if relay is None and bridge is None:
        return

    if not aug:
        aug = augeas_load()

    use_upstream_bridges = _are_upstream_bridges_enabled(aug)

    if relay and not use_upstream_bridges:
        aug.set(TOR_CONFIG + '/ORPort[1]', '9001')
        aug.set(TOR_CONFIG + '/ORPort[2]', '[::]:9001')
    elif relay is not None:
        aug.remove(TOR_CONFIG + '/ORPort')

    if bridge and not use_upstream_bridges:
        aug.set(TOR_CONFIG + '/BridgeRelay', '1')
        aug.set(TOR_CONFIG + '/ServerTransportPlugin',
                'obfs3,obfs4 exec /usr/bin/obfs4proxy')
        aug.set(TOR_CONFIG + '/ExtORPort', 'auto')
    elif bridge is not None:
        aug.remove(TOR_CONFIG + '/BridgeRelay')
        aug.remove(TOR_CONFIG + '/ServerTransportPlugin')
        aug.remove(TOR_CONFIG + '/ExtORPort')

    aug.save()


def _enable_hs(aug=None):
    """Enable Tor hidden service."""
    if not aug:
        aug = augeas_load()

    if _get_hidden_service(aug)['enabled']:
        return

    aug.set(TOR_CONFIG + '/HiddenServiceDir',
            '/var/lib/tor-instances/plinth/hidden_service')
    aug.set(TOR_CONFIG + '/HiddenServicePort[1]', '22 127.0.0.1:22')
    aug.set(TOR_CONFIG + '/HiddenServicePort[2]', '80 127.0.0.1:80')
    aug.set(TOR_CONFIG + '/HiddenServicePort[3]', '443 127.0.0.1:443')
    aug.save()


def _disable_hs(aug=None):
    """Disable Tor hidden service."""
    if not aug:
        aug = augeas_load()

    if not _get_hidden_service(aug)['enabled']:
        return

    aug.remove(TOR_CONFIG + '/HiddenServiceDir')
    aug.remove(TOR_CONFIG + '/HiddenServicePort')
    aug.save()


def _enable_apt_transport_tor():
    """Enable package download over Tor."""
    aug = get_augeas()
    for uri_path in iter_apt_uris(aug):
        uri_path = get_real_apt_uri_path(aug, uri_path)
        uri = aug.get(uri_path)
        if uri.startswith('http://') or uri.startswith('https://'):
            aug.set(uri_path, APT_TOR_PREFIX + uri)

    aug.save()


def _disable_apt_transport_tor():
    """Disable package download over Tor."""
    try:
        aug = get_augeas()
    except Exception:
        # Disable what we can, so APT is not unusable.
        pass

    for uri_path in iter_apt_uris(aug):
        uri_path = get_real_apt_uri_path(aug, uri_path)
        uri = aug.get(uri_path)
        if uri.startswith(APT_TOR_PREFIX):
            aug.set(uri_path, uri[len(APT_TOR_PREFIX):])

    aug.save()


def _update_port(name, number):
    """Update firewall service information for single port."""
    lines = """<?xml version="1.0" encoding="utf-8"?>
<service>
  <short>Tor - {0}</short>
  <port protocol="tcp" port="{1}"/>
</service>
"""
    try:
        with open(SERVICE_FILE.format(name), 'w',
                  encoding='utf-8') as service_file:
            service_file.writelines(lines.format(name, number))
    except FileNotFoundError:
        return


def _update_ports():
    """Update firewall service information."""
    ready = False
    tries = 0

    # port information may not be available immediately after Tor started
    while not ready:
        ports = _get_ports()
        ready = 'orport' in ports and 'obfs3' in ports and 'obfs4' in ports
        if ready:
            break

        tries += 1
        if tries >= 12:
            return

        time.sleep(10)

    for name, number in ports.items():
        _update_port(name, number)

    # XXX: We should ideally do firewalld reload instead.  However,
    # firewalld seems to fail to successfully reload sometimes.
    action_utils.service_restart('firewalld')


def augeas_load():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Tor/lens', 'Tor.lns')
    aug.set('/augeas/load/Tor/incl[last() + 1]',
            '/etc/tor/instances/plinth/torrc')
    aug.load()
    return aug
