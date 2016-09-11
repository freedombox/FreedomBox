#
# This file is part of Plinth.
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
Tor utility functions
"""

import augeas
import glob
import itertools
import json

from plinth import actions
from plinth import action_utils
from plinth.modules.names import SERVICES


APT_SOURCES_URI_PATHS = ('/files/etc/apt/sources.list/*/uri',
                         '/files/etc/apt/sources.list.d/*/*/uri')
APT_TOR_PREFIX = 'tor+'


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('tor@plinth')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('tor@plinth')


def get_status():
    """Return current Tor status."""
    output = actions.superuser_run('tor', ['get-status'])
    status = json.loads(output)

    hs_info = status['hidden_service']
    hs_services = []
    hs_virtports = [port['virtport'] for port in hs_info['ports']]
    for service_type in SERVICES:
        if str(service_type[2]) in hs_virtports:
            hs_services.append(service_type[0])

    # Filter out obfs3/4 ports when bridge relay is disabled
    ports = {service_type: port
             for service_type, port in status['ports'].items()
             if service_type not in ['obfs4', 'obfs3'] or
             status['bridge_relay_enabled']}

    return {'enabled': is_enabled(),
            'is_running': is_running(),
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
            'apt_transport_tor_enabled':
                _is_apt_transport_tor_enabled()
            }


def iter_apt_uris(aug):
    """Iterate over all the APT source URIs."""
    return itertools.chain.from_iterable([aug.match(path)
                                          for path in APT_SOURCES_URI_PATHS])


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


def _is_apt_transport_tor_enabled():
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
