# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Tor."""

import json
import logging

from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import action_utils
from plinth import app as app_module
from plinth import cfg, kvstore, menu
from plinth import setup as setup_module_  # Not setup_module, for pytest
from plinth.daemon import (Daemon, app_is_running, diagnose_netcat,
                           diagnose_port_listening)
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules import torproxy
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.names.components import DomainType
from plinth.modules.torproxy.utils import is_apt_transport_tor_enabled
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.privileged import service as service_privileged
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import manifest, privileged, utils

logger = logging.getLogger(__name__)

_description = [
    _('Tor is an anonymous communication system. You can learn more '
      'about it from the <a href="https://www.torproject.org/">Tor '
      'Project</a> website. For best protection when web surfing, the '
      'Tor Project recommends that you use the '
      '<a href="https://www.torproject.org/download/download-easy.html.en">'
      'Tor Browser</a>.'),
    _('This app provides relay services to contribute to Tor network and help '
      'others overcome censorship.'),
    format_lazy(
        _('This app provides an onion domain to expose {box_name} services '
          'via the Tor network. Using Tor browser, one can access {box_name} '
          'from the internet even when using an ISP that limits servers at '
          'home.'), box_name=_(cfg.box_name)),
]


class TorApp(app_module.App):
    """FreedomBox app for Tor."""

    app_id = 'tor'

    _version = 8

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               depends=['names'
                                        ], name=_('Tor'), icon_filename='tor',
                               short_description=_('Anonymity Network'),
                               description=_description, manual_page='Tor',
                               clients=manifest.clients, tags=manifest.tags,
                               donation_url='https://donate.torproject.org/')
        self.add(info)

        menu_item = menu.Menu('menu-tor', info.name, info.short_description,
                              info.icon_filename, 'tor:index',
                              parent_url_name='apps')
        self.add(menu_item)

        packages = Packages('packages-tor',
                            ['tor', 'tor-geoipdb', 'obfs4proxy'])
        self.add(packages)

        domain_type = DomainType('domain-type-tor', _('Tor Onion Service'),
                                 'tor:index', can_have_certificate=False)
        self.add(domain_type)

        firewall = Firewall('firewall-tor-relay', _('Tor Bridge Relay'),
                            ports=['tor-orport', 'tor-obfs3',
                                   'tor-obfs4'], is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-tor', 'tor@plinth', strict_check=True)
        self.add(daemon)

        webserver = Webserver('webserver-onion-location',
                              'onion-location-freedombox')
        self.add(webserver)

        users_and_groups = UsersAndGroups('users-and-groups-tor',
                                          reserved_usernames=['debian-tor'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-tor', **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        # Register onion service name with Name Services module.
        if (not self.needs_setup() and self.is_enabled()
                and app_is_running(self)):
            status = utils.get_status(initialized=False)
            hostname = status['hs_hostname']
            services = [int(port['virtport']) for port in status['hs_ports']]

            if status['hs_enabled'] and status['hs_hostname']:
                domain_added.send_robust(sender='tor',
                                         domain_type='domain-type-tor',
                                         name=hostname, services=services)

    def enable(self):
        """Enable the app and update firewall ports."""
        service_privileged.unmask('tor@plinth')
        super().enable()
        privileged.update_ports()
        update_hidden_service_domain()

    def disable(self):
        """Disable the app and remove HS domain."""
        super().disable()
        service_privileged.mask('tor@plinth')
        update_hidden_service_domain()

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()

        results.extend(_diagnose_control_port())

        status = utils.get_status()
        ports = status['ports']

        if status['relay_enabled']:
            results.append(
                DiagnosticCheck(
                    'tor-port-relay', gettext_noop('Tor relay port available'),
                    Result.PASSED if 'orport' in ports else Result.FAILED))
            if 'orport' in ports:
                results.append(
                    diagnose_port_listening(int(ports['orport']), 'tcp4'))
                results.append(
                    diagnose_port_listening(int(ports['orport']), 'tcp6'))

        if status['bridge_relay_enabled']:
            results.append(
                DiagnosticCheck(
                    'tor-port-obfs3',
                    gettext_noop('Obfs3 transport registered'),
                    Result.PASSED if 'obfs3' in ports else Result.FAILED))
            if 'obfs3' in ports:
                results.append(
                    diagnose_port_listening(int(ports['obfs3']), 'tcp4'))
                results.append(
                    diagnose_port_listening(int(ports['obfs3']), 'tcp6'))

            results.append(
                DiagnosticCheck(
                    'tor-port-obfs4',
                    gettext_noop('Obfs4 transport registered'),
                    Result.PASSED if 'obfs4' in ports else Result.FAILED))
            if 'obfs4' in ports:
                results.append(
                    diagnose_port_listening(int(ports['obfs4']), 'tcp4'))
                results.append(
                    diagnose_port_listening(int(ports['obfs4']), 'tcp6'))

        if status['hs_enabled']:
            hs_hostname = status['hs_hostname'].split('.onion')[0]
            results.append(
                DiagnosticCheck(
                    'tor-onion-version',
                    gettext_noop('Onion service is version 3'), Result.PASSED
                    if len(hs_hostname) == 56 else Result.FAILED))

        return results

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup(old_version)
        status = utils.get_status()
        update_hidden_service_domain(status)

        # Enable/disable Onion-Location component based on app status.
        # Component was introduced in version 6.
        if old_version and old_version < 6:
            daemon_component = self.get_component('daemon-tor')
            component = self.get_component('webserver-onion-location')
            if daemon_component.is_enabled():
                logger.info('Enabling Onion-Location component')
                component.enable()
            else:
                logger.info('Disabling Onion-Location component')
                component.disable()

        # The SOCKS proxy and "Download software packages using Tor" features
        # were moved into a new app, Tor Proxy, in version 7. If Tor is
        # enabled, then store the relevant configuration, and install Tor
        # Proxy.
        if old_version and old_version < 7 and self.is_enabled():
            logger.info('Tor Proxy app will be installed')
            config = {
                'use_upstream_bridges': status['use_upstream_bridges'],
                'upstream_bridges': status['upstream_bridges'],
                'apt_transport_tor': is_apt_transport_tor_enabled()
            }
            kvstore.set(torproxy.PREINSTALL_CONFIG_KEY, json.dumps(config))
            # This creates the operation, which will run after the current
            # operation (Tor setup) is completed.
            setup_module_.run_setup_on_app('torproxy')

        # Version 8 masks the tor@plinth service when disabling the app to
        # prevent the service starting by the Tor master service after system
        # reboot.
        if old_version and old_version < 8 and not self.is_enabled():
            self.disable()

        if not old_version:
            logger.info('Enabling Tor app')
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


def update_hidden_service_domain(status=None):
    """Update onion service domain with Name Services module."""
    if not status:
        status = utils.get_status()

    domain_removed.send_robust(sender='tor', domain_type='domain-type-tor')

    if status['enabled'] and status['is_running'] and \
       status['hs_enabled'] and status['hs_hostname']:
        services = [int(port['virtport']) for port in status['hs_ports']]
        domain_added.send_robust(sender='tor', domain_type='domain-type-tor',
                                 name=status['hs_hostname'], services=services)


def _diagnose_control_port() -> list[DiagnosticCheck]:
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
            diagnose_netcat(str(address['address']), 9051,
                            remote_input='QUIT\n', negate=negate))

    return results
