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
Plinth module to configure Tor.
"""

import augeas
from django.utils.translation import ugettext_lazy as _
import glob
import itertools

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.modules.names import SERVICES
from plinth.signals import domain_added


version = 1

depends = ['apps', 'names']

title = _('Anonymity Network (Tor)')

description = [
    _('Tor is an anonymous communication system. You can learn more '
      'about it from the <a href="https://www.torproject.org/">Tor '
      'Project</a> website. For best protection when web surfing, the '
      'Tor Project recommends that you use the '
      '<a href="https://www.torproject.org/download/download-easy.html.en">'
      'Tor Browser</a>.')
]

socks_service = None
bridge_service = None

APT_SOURCES_URI_PATHS = ('/files/etc/apt/sources.list/*/uri',
                         '/files/etc/apt/sources.list.d/*/*/uri')
APT_TOR_PREFIX = 'tor+'


def init():
    """Initialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-eye-close', 'tor:index', 100)

    global socks_service
    socks_service = service_module.Service(
        'tor-socks', _('Tor Anonymity Network'),
        is_external=False, enabled=is_enabled())

    global bridge_service
    bridge_service = service_module.Service(
        'tor-bridge', _('Tor Bridge Relay'),
        ports=['tor-orport', 'tor-obfs3', 'tor-obfs4'],
        is_external=True, enabled=is_enabled())

    # Register hidden service name with Name Services module.
    (hs_enabled, hs_hostname, hs_ports) = get_hs()

    if is_enabled() and is_running() and hs_enabled and hs_hostname:
        hs_services = []
        for service_type in SERVICES:
            if str(service_type[2]) in hs_ports:
                hs_services.append(service_type[0])
    else:
        hs_hostname = None
        hs_services = None

    domain_added.send_robust(
        sender='tor', domain_type='hiddenservice',
        name=hs_hostname, description=_('Tor Hidden Service'),
        services=hs_services)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['tor', 'tor-geoipdb', 'torsocks', 'obfs4proxy',
                    'apt-transport-tor'])
    helper.call('post', actions.superuser_run, 'tor', ['setup'])
    helper.call('post', actions.superuser_run, 'tor',
                ['configure', '--apt-transport-tor', 'enable'])
    helper.call('post', socks_service.notify_enabled, None, True)
    helper.call('post', bridge_service.notify_enabled, None, True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('tor')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('tor')


def get_status():
    """Return current Tor status."""
    output = actions.superuser_run('tor', ['get-ports'])
    port_info = output.split('\n')
    ports = {}
    for line in port_info:
        try:
            (key, val) = line.split()
            ports[key] = val
        except ValueError:
            continue

    (hs_enabled, hs_hostname, hs_ports) = get_hs()

    return {'enabled': is_enabled(),
            'is_running': is_running(),
            'ports': ports,
            'hs_enabled': hs_enabled,
            'hs_hostname': hs_hostname,
            'hs_ports': hs_ports,
            'apt_transport_tor_enabled': is_apt_transport_tor_enabled()}


def get_hs():
    """Return hidden service status."""
    output = actions.superuser_run('tor', ['get-hs'])
    output = output.strip()
    if output == '':
        hs_enabled = False
        hs_hostname = 'Not Configured'
        hs_ports = ''
    elif output == 'error':
        hs_enabled = False
        hs_hostname = 'Not available (Run Tor at least once)'
        hs_ports = ''
    else:
        hs_enabled = True
        hs_info = output.split()
        hs_hostname = hs_info[0]
        hs_ports = hs_info[1]

    return (hs_enabled, hs_hostname, hs_ports)


def get_augeas():
    """Return an instance of Augeaus for processing APT configuration."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Aptsources/lens', 'Aptsources.lns')
    aug.set('/augeas/load/Aptsources/incl[last() + 1]', '/etc/apt/sources.list')
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
