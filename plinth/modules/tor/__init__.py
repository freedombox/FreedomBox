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

from django.utils.translation import ugettext_lazy as _
import json

from plinth import actions
from plinth import action_utils
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.modules.names import SERVICES
from plinth.signals import domain_added, domain_removed

from . import utils


version = 2

depends = ['names']

managed_packages = ['tor', 'tor-geoipdb', 'torsocks', 'obfs4proxy',
                    'apt-transport-tor']

title = ('Anonymity Network \n (Tor)')

description = [
    _('Tor is an anonymous communication system. You can learn more '
      'about it from the <a href="https://www.torproject.org/">Tor '
      'Project</a> website. For best protection when web surfing, the '
      'Tor Project recommends that you use the '
      '<a href="https://www.torproject.org/download/download-easy.html.en">'
      'Tor Browser</a>.')
]

reserved_usernames = ['debian-tor']

socks_service = None
bridge_service = None


def init():
    """Initialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-eye-close', 'tor:index')

    setup_helper = globals()['setup_helper']
    needs_setup = setup_helper.get_state() == 'needs-setup'

    if not needs_setup:
        global socks_service
        socks_service = service_module.Service(
            'tor-socks', _('Tor Anonymity Network'), ports=['tor-socks'],
            is_external=False, is_enabled=utils.is_enabled,
            is_running=utils.is_running)

        global bridge_service
        bridge_service = service_module.Service(
            'tor-bridge', _('Tor Bridge Relay'),
            ports=['tor-orport', 'tor-obfs3', 'tor-obfs4'],
            is_external=True, is_enabled=utils.is_enabled,
            is_running=utils.is_running)

        # Register hidden service name with Name Services module.
        status = utils.get_status()
        hostname = status['hs_hostname']
        hs_virtports = [port['virtport'] for port in status['hs_ports']]

        if status['enabled'] and status['is_running'] and \
           status['hs_enabled'] and status['hs_hostname']:
            hs_services = []
            for service_type in SERVICES:
                if str(service_type[2]) in hs_virtports:
                    hs_services.append(service_type[0])
        else:
            hostname = None
            hs_services = None

        domain_added.send_robust(
            sender='tor', domain_type='hiddenservice',
            name=hostname, description=_('Tor Hidden Service'),
            services=hs_services)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'tor', ['setup'])
    helper.call('post', actions.superuser_run, 'tor',
                ['configure', '--apt-transport-tor', 'enable'])

    global socks_service
    if socks_service is None:
        socks_service = service_module.Service(
            'tor-socks', _('Tor Anonymity Network'), ports=['tor-socks'],
            is_external=False, is_enabled=utils.is_enabled,
            is_running=utils.is_running)
    helper.call('post', socks_service.notify_enabled, None, True)

    global bridge_service
    if bridge_service is None:
        bridge_service = service_module.Service(
            'tor-bridge', _('Tor Bridge Relay'),
            ports=['tor-orport', 'tor-obfs3', 'tor-obfs4'],
            is_external=True, is_enabled=utils.is_enabled,
            is_running=utils.is_running)
    helper.call('post', bridge_service.notify_enabled, None, True)

    helper.call('post', update_hidden_service_domain)


def update_hidden_service_domain(status=None):
    """Update HS domain with Name Services module."""
    if not status:
        status = utils.get_status()

    domain_removed.send_robust(
        sender='tor', domain_type='hiddenservice')

    if status['enabled'] and status['is_running'] and \
       status['hs_enabled'] and status['hs_hostname']:
        domain_added.send_robust(
            sender='tor', domain_type='hiddenservice',
            name=status['hs_hostname'], description=_('Tor Hidden Service'),
            services=status['hs_services'])


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

    output = actions.superuser_run('tor', ['get-status'])
    ports = json.loads(output)['ports']

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
