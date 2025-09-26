# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Tor Proxy service."""

import logging
import os
import shutil
import subprocess
from typing import Any

import augeas

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.torproxy.utils import (APT_TOR_PREFIX, get_augeas,
                                           iter_apt_uris)

logger = logging.getLogger(__name__)

INSTANCE_NAME = 'fbxproxy'
SERVICE_FILE = '/etc/firewalld/services/tor-{0}.xml'
SERVICE_NAME = f'tor@{INSTANCE_NAME}'
TORPROXY_CONFIG = f'/etc/tor/instances/{INSTANCE_NAME}/torrc'
TORPROXY_CONFIG_AUG = f'/files/{TORPROXY_CONFIG}'


@privileged
def setup():
    """Setup Tor configuration."""
    # Disable default Tor service.
    action_utils.service_disable('tor@default')
    # Mask the service to prevent re-enabling it by the Tor master service.
    action_utils.service_mask('tor@default')

    subprocess.run(['tor-instance-create', INSTANCE_NAME], check=True)

    # Remove line starting with +SocksPort, since our augeas lens
    # doesn't handle it correctly.
    with open(TORPROXY_CONFIG, 'r', encoding='utf-8') as torrc:
        torrc_lines = torrc.readlines()
    with open(TORPROXY_CONFIG, 'w', encoding='utf-8') as torrc:
        for line in torrc_lines:
            if not line.startswith('+'):
                torrc.write(line)

    aug = augeas_load()

    aug.set(TORPROXY_CONFIG_AUG + '/SocksPort[1]', '[::]:9050')
    aug.set(TORPROXY_CONFIG_AUG + '/SocksPort[2]', '0.0.0.0:9050')
    aug.set(TORPROXY_CONFIG_AUG + '/VirtualAddrNetworkIPv4', '10.192.0.0/10')
    aug.set(TORPROXY_CONFIG_AUG + '/AutomapHostsOnResolve', '1')
    aug.set(TORPROXY_CONFIG_AUG + '/TransPort[1]', '127.0.0.1:9040')
    aug.set(TORPROXY_CONFIG_AUG + '/TransPort[2]', '[::1]:9040')
    aug.set(TORPROXY_CONFIG_AUG + '/DNSPort[1]', '127.0.0.1:9053')
    aug.set(TORPROXY_CONFIG_AUG + '/DNSPort[2]', '[::1]:9053')

    aug.save()

    if action_utils.service_is_running(SERVICE_NAME):
        action_utils.service_restart(SERVICE_NAME)


@privileged
def configure(use_upstream_bridges: bool | None = None,
              upstream_bridges: str | None = None,
              apt_transport_tor: bool | None = None):
    """Configure Tor."""
    aug = augeas_load()

    _use_upstream_bridges(use_upstream_bridges, aug=aug)

    if upstream_bridges:
        _set_upstream_bridges(upstream_bridges, aug=aug)

    if apt_transport_tor:
        _enable_apt_transport_tor()
    elif apt_transport_tor is not None:
        _disable_apt_transport_tor()


@privileged
def restart():
    """Restart Tor."""
    if (action_utils.service_is_enabled(SERVICE_NAME, strict_check=True)
            and action_utils.service_is_running(SERVICE_NAME)):
        action_utils.service_restart(SERVICE_NAME)


@privileged
def get_status() -> dict[str, bool | str | dict[str, Any]]:
    """Return dict with Tor Proxy status."""
    aug = augeas_load()
    return {
        'use_upstream_bridges': _are_upstream_bridges_enabled(aug),
        'upstream_bridges': _get_upstream_bridges(aug)
    }


def _are_upstream_bridges_enabled(aug) -> bool:
    """Return whether upstream bridges are being used."""
    use_bridges = aug.get(TORPROXY_CONFIG_AUG + '/UseBridges')
    return use_bridges == '1'


def _get_upstream_bridges(aug) -> str:
    """Return upstream bridges separated by newlines."""
    matches = aug.match(TORPROXY_CONFIG_AUG + '/Bridge')
    bridges = [aug.get(match) for match in matches]
    return '\n'.join(bridges)


def _use_upstream_bridges(use_upstream_bridges: bool | None = None, aug=None):
    """Enable use of upstream bridges."""
    if use_upstream_bridges is None:
        return

    if not aug:
        aug = augeas_load()

    if use_upstream_bridges:
        aug.set(TORPROXY_CONFIG_AUG + '/UseBridges', '1')
    else:
        aug.set(TORPROXY_CONFIG_AUG + '/UseBridges', '0')

    aug.save()


def _set_upstream_bridges(upstream_bridges=None, aug=None):
    """Set list of upstream bridges."""
    if upstream_bridges is None:
        return

    if not aug:
        aug = augeas_load()

    aug.remove(TORPROXY_CONFIG_AUG + '/Bridge')
    if upstream_bridges:
        bridges = [bridge.strip() for bridge in upstream_bridges.split('\n')]
        bridges = [bridge for bridge in bridges if bridge]
        for bridge in bridges:
            parts = [part for part in bridge.split() if part]
            bridge = ' '.join(parts)
            aug.set(TORPROXY_CONFIG_AUG + '/Bridge[last() + 1]',
                    bridge.strip())

    aug.set(TORPROXY_CONFIG_AUG + '/ClientTransportPlugin',
            'obfs3,scramblesuit,obfs4 exec /usr/bin/obfs4proxy')

    aug.save()


def _enable_apt_transport_tor():
    """Enable package download over Tor."""
    aug = get_augeas()
    for uri_path in iter_apt_uris(aug):
        uri = aug.get(uri_path)
        if uri.startswith('http://') or uri.startswith('https://'):
            aug.set(uri_path, APT_TOR_PREFIX + uri)

    aug.save()


def _disable_apt_transport_tor():
    """Disable package download over Tor."""
    aug = get_augeas(raise_exception=False)
    for uri_path in iter_apt_uris(aug):
        uri = aug.get(uri_path)
        if uri.startswith(APT_TOR_PREFIX):
            aug.set(uri_path, uri[len(APT_TOR_PREFIX):])

    aug.save()


def augeas_load():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Tor/lens', 'Tor.lns')
    aug.set('/augeas/load/Tor/incl[last() + 1]', TORPROXY_CONFIG)
    aug.load()
    return aug


@privileged
def uninstall():
    """Remove fbxproxy instance."""
    directories = [
        f'/etc/tor/instances/{INSTANCE_NAME}/',
        f'/var/lib/tor-instances/{INSTANCE_NAME}/',
        f'/var/run/tor-instances/{INSTANCE_NAME}/'
    ]
    for directory in directories:
        shutil.rmtree(directory, ignore_errors=True)

    os.unlink(f'/var/run/tor-instances/{INSTANCE_NAME}.defaults')
    action_utils.service_unmask(SERVICE_NAME)
