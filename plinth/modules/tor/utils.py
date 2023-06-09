# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tor utility functions."""

from plinth import app as app_module
from plinth.daemon import app_is_running
from plinth.modules.names.components import DomainName

from . import privileged


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
    }
