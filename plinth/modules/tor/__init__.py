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
Plinth module to configure Tor
"""

from django.utils.translation import ugettext as _

from . import tor
from .tor import init
from plinth import actions
from plinth import action_utils

__all__ = ['tor', 'init']

depends = ['plinth.modules.apps', 'plinth.modules.names']


def diagnose():
    """Run diagnostics and return the results."""
    results = []
    results.append(action_utils.diagnose_port_listening(9050, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(9050, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(9040, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(9040, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(9053, 'udp4'))
    results.append(action_utils.diagnose_port_listening(9053, 'udp6'))

    results.extend(_diagnose_control_port())

    output = actions.superuser_run('tor', ['get-ports'])
    ports = [line.split() for line in output.splitlines()]
    ports = {port_type: int(port) for port_type, port in ports}

    results.append([_('Tor relay port available'),
                    'passed' if 'orport' in ports else 'failed'])
    if 'orport' in ports:
        results.append(action_utils.diagnose_port_listening(ports['orport'],
                                                            'tcp4'))
        results.append(action_utils.diagnose_port_listening(ports['orport'],
                                                            'tcp6'))

    results.append([_('Obfs3 transport registered'),
                    'passed' if 'obfs3' in ports else 'failed'])
    if 'obfs3' in ports:
        results.append(action_utils.diagnose_port_listening(ports['obfs3'],
                                                            'tcp4'))

    results.append([_('Obfs4 transport registered'),
                    'passed' if 'obfs4' in ports else 'failed'])
    if 'obfs4' in ports:
        results.append(action_utils.diagnose_port_listening(
            ports['obfs4'], 'tcp4'))

    results.append(_diagnose_url_via_tor('http://www.debian.org', '4'))
    results.append(_diagnose_url_via_tor('http://www.debian.org', '6'))

    results.append(_diagnose_tor_use('https://check.torproject.org', '4'))
    results.append(_diagnose_tor_use('https://check.torproject.org', '6'))

    return results


def _diagnose_control_port():
    """Diagnose whether Tor control port is open on 127.0.0.1 only."""
    results = []

    addresses = action_utils.get_ip_addresses()
    for address in addresses:
        if address['kind'] != '4':
            continue

        negate = True
        if address['address'] == '127.0.0.1':
            negate = False

        results.append(action_utils.diagnose_netcat(
            address['address'], 9051, input='QUIT\n', negate=negate))

    return results


def _diagnose_url_via_tor(url, kind=None):
    """Diagnose whether a URL is reachable via Tor."""
    result = action_utils.diagnose_url(url, kind=kind, wrapper='torsocks')
    result[0] = _('Access URL {url} on tcp{kind} via Tor') \
        .format(url=url, kind=kind)

    return result


def _diagnose_tor_use(url, kind=None):
    """Diagnose whether webpage at URL reports that we are using Tor."""
    expected_output = 'Congratulations. This browser is configured to use Tor.'
    result = action_utils.diagnose_url(url, kind=kind, wrapper='torsocks',
                                       expected_output=expected_output)
    result[0] = _('Confirm Tor usage at {url} on tcp{kind}') \
        .format(url=url, kind=kind)

    return result
