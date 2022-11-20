# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tor utility functions."""

import itertools

import augeas

from plinth import app as app_module
from plinth.daemon import app_is_running
from plinth.modules.names.components import DomainName

from . import privileged

APT_SOURCES_URI_PATHS = ('/files/etc/apt/sources.list/*/uri',
                         '/files/etc/apt/sources.list.d/*/*/uri',
                         '/files/etc/apt/sources.list.d/*/*/URIs/*')
APT_TOR_PREFIX = 'tor+'


def get_status(initialized=True):
    """Return current Tor status."""
    status = privileged.get_status()

    hs_info = status['hidden_service']
    hs_services = []
    if hs_info['hostname']:
        try:
            domain = DomainName.get('domain-tor-' + hs_info['hostname'])
        except KeyError:
            pass
        else:
            hs_services = domain.get_readable_services()

    # Filter out obfs3/4 ports when bridge relay is disabled
    ports = {
        service_type: port
        for service_type, port in status['ports'].items()
        if service_type not in ['obfs4', 'obfs3']
        or status['bridge_relay_enabled']
    }

    app = app_module.App.get('tor')
    return {
        'enabled': app.is_enabled() if initialized else False,
        'is_running': app_is_running(app) if initialized else False,
        'use_upstream_bridges': status['use_upstream_bridges'],
        'upstream_bridges': status['upstream_bridges'],
        'relay_enabled': status['relay_enabled'],
        'bridge_relay_enabled': status['bridge_relay_enabled'],
        'ports': ports,
        'hs_enabled': hs_info['enabled'],
        'hs_status': hs_info['status'],
        'hs_hostname': hs_info['hostname'],
        'hs_ports': hs_info['ports'],
        'hs_services': hs_services,
        'apt_transport_tor_enabled': is_apt_transport_tor_enabled()
    }


def iter_apt_uris(aug):
    """Iterate over all the APT source URIs."""
    return itertools.chain.from_iterable(
        [aug.match(path) for path in APT_SOURCES_URI_PATHS])


def get_augeas():
    """Return an instance of Augeaus for processing APT configuration."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Aptsources/lens', 'Aptsources.lns')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]',
            '/etc/apt/sources.list')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]',
            '/etc/apt/sources.list.d/*.list')
    aug.set('/augeas/load/Aptsources822/lens', 'Aptsources822.lns')
    aug.set('/augeas/load/Aptsources822/incl[last() + 1]',
            '/etc/apt/sources.list.d/*.sources')
    aug.load()

    # Check for any errors in parsing sources lists.
    if aug.match('/augeas/files/etc/apt/sources.list/error') or \
       aug.match('/augeas/files/etc/apt/sources.list.d//error'):
        raise Exception('Error parsing sources list')

    return aug


def is_apt_transport_tor_enabled():
    """Return whether APT is set to download packages over Tor."""
    try:
        aug = get_augeas()
    except Exception:
        # If there was an error with parsing.
        return False

    for uri_path in iter_apt_uris(aug):
        uri = aug.get(uri_path)
        if not uri.startswith(APT_TOR_PREFIX) and \
           (uri.startswith('http://') or uri.startswith('https://')):
            return False

    return True
