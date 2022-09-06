# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tor utility functions
"""

import glob
import itertools
import json

import augeas

from plinth import actions
from plinth import app as app_module
from plinth.daemon import app_is_running
from plinth.modules.names.components import DomainName

APT_SOURCES_URI_PATHS = ('/files/etc/apt/sources.list/*/uri',
                         '/files/etc/apt/sources.list.d/*/*/uri')
APT_TOR_PREFIX = 'tor+'


def get_status(initialized=True):
    """Return current Tor status."""
    output = actions.superuser_run('tor', ['get-status'])
    status = json.loads(output)

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


def get_real_apt_uri_path(aug, path):
    """Return the actual path which contains APT URL.

    XXX: This is a workaround for Augeas bug parsing Apt source files
    with '[options]'.  Remove this workaround after Augeas lens is
    fixed.
    """
    uri = aug.get(path)
    if uri[0] == '[':
        parent_path = path.rsplit('/', maxsplit=1)[0]
        skipped = False
        for child_path in aug.match(parent_path + '/*')[1:]:
            if skipped:
                return child_path

            value = aug.get(child_path)
            if value[-1] == ']':
                skipped = True

    return path


def get_augeas():
    """Return an instance of Augeaus for processing APT configuration."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Aptsources/lens', 'Aptsources.lns')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]',
            '/etc/apt/sources.list')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]',
            '/etc/apt/sources.list.d/*.list')
    aug.load()

    # Currently, augeas does not handle Deb822 format, it error out.
    if aug.match('/augeas/files/etc/apt/sources.list/error') or \
       aug.match('/augeas/files/etc/apt/sources.list.d//error'):
        raise Exception('Error parsing sources list')

    # Starting with Apt 1.1, /etc/apt/sources.list.d/*.sources will
    # contain files with Deb822 format.  If they are found, error out
    # for now.  XXX: Provide proper support Deb822 format with a new
    # Augeas lens.
    if glob.glob('/etc/apt/sources.list.d/*.sources'):
        raise Exception('Can not handle Deb822 source files')

    return aug


def is_apt_transport_tor_enabled():
    """Return whether APT is set to download packages over Tor."""
    try:
        aug = get_augeas()
    except Exception:
        # If there was an error with parsing or there are Deb822
        # files.
        return False

    for uri_path in iter_apt_uris(aug):
        uri_path = get_real_apt_uri_path(aug, uri_path)
        uri = aug.get(uri_path)
        if not uri.startswith(APT_TOR_PREFIX) and \
           (uri.startswith('http://') or uri.startswith('https://')):
            return False

    return True
