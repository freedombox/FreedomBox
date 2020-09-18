# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Tor.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import menu
from plinth.daemon import (Daemon, app_is_running, diagnose_netcat,
                           diagnose_port_listening)
from plinth.modules.apache.components import diagnose_url
from plinth.modules.firewall.components import Firewall
from plinth.modules.names.components import DomainType
from plinth.modules.users.components import UsersAndGroups
from plinth.signals import domain_added, domain_removed

from . import utils
from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 5

depends = ['names']

managed_packages = [
    'tor', 'tor-geoipdb', 'torsocks', 'obfs4proxy', 'apt-transport-tor'
]

managed_services = ['tor@plinth']

_description = [
    _('Tor is an anonymous communication system. You can learn more '
      'about it from the <a href="https://www.torproject.org/">Tor '
      'Project</a> website. For best protection when web surfing, the '
      'Tor Project recommends that you use the '
      '<a href="https://www.torproject.org/download/download-easy.html.en">'
      'Tor Browser</a>.')
]

app = None


class TorApp(app_module.App):
    """FreedomBox app for Tor."""

    app_id = 'tor'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Tor'), icon_filename='tor',
                               short_description=_('Anonymity Network'),
                               description=_description, manual_page='Tor',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-tor', info.name, info.short_description,
                              info.icon_filename, 'tor:index',
                              parent_url_name='apps')
        self.add(menu_item)

        domain_type = DomainType('domain-type-tor', _('Tor Onion Service'),
                                 'tor:index', can_have_certificate=False)
        self.add(domain_type)

        firewall = Firewall('firewall-tor-socks', _('Tor Socks Proxy'),
                            ports=['tor-socks'], is_external=False)
        self.add(firewall)

        firewall = Firewall('firewall-tor-relay', _('Tor Bridge Relay'),
                            ports=['tor-orport', 'tor-obfs3',
                                   'tor-obfs4'], is_external=True)
        self.add(firewall)

        daemon = Daemon(
            'daemon-tor', managed_services[0], strict_check=True,
            listen_ports=[(9050, 'tcp4'), (9050, 'tcp6'), (9040, 'tcp4'),
                          (9040, 'tcp6'), (9053, 'udp4'), (9053, 'udp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-tor',
                                          reserved_usernames=['debian-tor'])
        self.add(users_and_groups)

        # Register hidden service name with Name Services module.
        if self.is_enabled() and app_is_running(self):
            status = utils.get_status(initialized=False)
            hostname = status['hs_hostname']
            services = [int(port['virtport']) for port in status['hs_ports']]

            if status['hs_enabled'] and status['hs_hostname']:
                domain_added.send_robust(sender='tor',
                                         domain_type='domain-type-tor',
                                         name=hostname, services=services)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()

        results.extend(_diagnose_control_port())

        output = actions.superuser_run('tor', ['get-status'])
        ports = json.loads(output)['ports']

        results.append([
            _('Tor relay port available'),
            'passed' if 'orport' in ports else 'failed'
        ])
        if 'orport' in ports:
            results.append(
                diagnose_port_listening(int(ports['orport']), 'tcp4'))
            results.append(
                diagnose_port_listening(int(ports['orport']), 'tcp6'))

        results.append([
            _('Obfs3 transport registered'),
            'passed' if 'obfs3' in ports else 'failed'
        ])
        if 'obfs3' in ports:
            results.append(diagnose_port_listening(int(ports['obfs3']),
                                                   'tcp4'))
            results.append(diagnose_port_listening(int(ports['obfs3']),
                                                   'tcp6'))

        results.append([
            _('Obfs4 transport registered'),
            'passed' if 'obfs4' in ports else 'failed'
        ])
        if 'obfs4' in ports:
            results.append(diagnose_port_listening(int(ports['obfs4']),
                                                   'tcp4'))
            results.append(diagnose_port_listening(int(ports['obfs4']),
                                                   'tcp6'))

        results.append(_diagnose_url_via_tor('http://www.debian.org', '4'))
        results.append(_diagnose_url_via_tor('http://www.debian.org', '6'))

        results.append(_diagnose_tor_use('https://check.torproject.org', '4'))
        results.append(_diagnose_tor_use('https://check.torproject.org', '6'))

        return results


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call(
        'post', actions.superuser_run, 'tor',
        ['setup', '--old-version', str(old_version)])
    if not old_version:
        helper.call('post', actions.superuser_run, 'tor',
                    ['configure', '--apt-transport-tor', 'enable'])

    helper.call('post', update_hidden_service_domain)
    helper.call('post', app.enable)


def update_hidden_service_domain(status=None):
    """Update HS domain with Name Services module."""
    if not status:
        status = utils.get_status()

    domain_removed.send_robust(sender='tor', domain_type='domain-type-tor')

    if status['enabled'] and status['is_running'] and \
       status['hs_enabled'] and status['hs_hostname']:
        services = [int(port['virtport']) for port in status['hs_ports']]
        domain_added.send_robust(sender='tor', domain_type='domain-type-tor',
                                 name=status['hs_hostname'], services=services)


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

        results.append(
            diagnose_netcat(address['address'], 9051, input='QUIT\n',
                            negate=negate))

    return results


def _diagnose_url_via_tor(url, kind=None):
    """Diagnose whether a URL is reachable via Tor."""
    result = diagnose_url(url, kind=kind, wrapper='torsocks')
    result[0] = _('Access URL {url} on tcp{kind} via Tor') \
        .format(url=url, kind=kind)

    return result


def _diagnose_tor_use(url, kind=None):
    """Diagnose whether webpage at URL reports that we are using Tor."""
    expected_output = 'Congratulations. This browser is configured to use Tor.'
    result = diagnose_url(url, kind=kind, wrapper='torsocks',
                          expected_output=expected_output)
    result[0] = _('Confirm Tor usage at {url} on tcp{kind}') \
        .format(url=url, kind=kind)

    return result
