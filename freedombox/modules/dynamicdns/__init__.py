# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure ez-ipupdate client.
"""

import json
import logging
import subprocess
import time
from typing import Any, Literal, Tuple

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, glib, kvstore, menu
from plinth.modules.backups.components import BackupRestore
from plinth.modules.names.components import DomainType
from plinth.modules.privacy import lookup_public_address
from plinth.modules.users.components import UsersAndGroups
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import generic, gnudip, manifest

logger = logging.getLogger(__name__)

_description = [
    format_lazy(
        _('If your Internet provider changes your IP address periodically '
          '(i.e. every 24h), it may be hard for others to find you on the '
          'Internet. This will prevent others from finding services which are '
          'provided by this {box_name}.'), box_name=_(cfg.box_name)),
    _('The solution is to assign a DNS name to your IP address and '
      'update the DNS name every time your IP is changed by your '
      'Internet provider. Dynamic DNS allows you to push your current '
      'public IP address to a '
      '<a href=\'http://gnudip2.sourceforge.net/\' target=\'_blank\'> '
      'GnuDIP</a> server. Afterwards, the server will assign your DNS name '
      'to the new IP, and if someone from the Internet asks for your DNS '
      'name, they will get a response with your current IP address.'),
    _('If you are looking for a free dynamic DNS account, you may find a free '
      'GnuDIP service at <a href=\'https://ddns.freedombox.org\' '
      'target=\'_blank\'>ddns.freedombox.org</a>. With this service, you also '
      'get unlimited subdomains (with wildcards option enabled in account '
      'settings). To use a subdomain, add it as a static domain in the Names '
      'app.'),
    _('Alternatively, you may find a free update URL based service at '
      '<a href=\'http://freedns.afraid.org/\' '
      'target=\'_blank\'>freedns.afraid.org</a>.'),
    _('This service uses an external service to lookup public IP address. '
      'This can be configured in the privacy app.'),
]


class DynamicDNSApp(app_module.App):
    """FreedomBox app for Dynamic DNS."""

    app_id = 'dynamicdns'

    _version = 2

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, depends=['names'],
                               name=_('Dynamic DNS Client'), icon='fa-refresh',
                               description=_description,
                               manual_page='DynamicDNS', tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-dynamicdns', info.name, info.icon,
                              info.tags, 'dynamicdns:index',
                              parent_url_name='system:visibility', order=20)
        self.add(menu_item)

        enable_state = app_module.EnableState('enable-state-dynamicdns')
        self.add(enable_state)

        domain_type = DomainType('domain-type-dynamic', _('Dynamic Domain'),
                                 edit_url='dynamicdns:domain-edit',
                                 delete_url='dynamicdns:domain-delete',
                                 add_url='dynamicdns:domain-add',
                                 can_have_certificate=True, priority=70)
        self.add(domain_type)

        users_and_groups = UsersAndGroups('users-and-groups-dynamicdns',
                                          reserved_usernames=['ez-ipupd'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-dynamicdns',
                                       **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        config = get_config()
        if self.is_enabled():
            for domain_name in config['domains']:
                notify_domain_added(domain_name)

        # Check every 5 minutes to perform dynamic DNS updates.
        glib.schedule(300, update_dns)

    def enable(self):
        """Send domain signals after enabling the app."""
        super().enable()
        config = get_config()
        for domain_name in config['domains']:
            notify_domain_added(domain_name)

    def disable(self):
        """Send domain signals before disabling the app."""
        config = get_config()
        for domain_name in config['domains']:
            notify_domain_removed(domain_name)

        super().disable()

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()


def _lookup_public_address(ip_type: Literal['ipv4', 'ipv6']):
    """Return the IP address by querying an external server."""
    try:
        return lookup_public_address(ip_type)
    except Exception:
        return None


def _query_dns_address(domain: str, ip_type: Literal['ipv4',
                                                     'ipv6']) -> str | None:
    """Return the IP address in the DNS records."""
    ip_option = 'AAAA' if ip_type == 'ipv6' else 'A'
    try:
        output = subprocess.check_output(['host', '-t', ip_option, domain])
        return output.decode().split(' ')[-1].strip().lower()
    except subprocess.CalledProcessError as exception:
        logger.warning('Unable to lookup DNS for host %s: %s', domain,
                       exception)
        return None


def _check_uptodate_for_ip_type(
        domain: dict[str, Any],
        ip_type: Literal['ipv4', 'ipv6']) -> Tuple[bool, str | None, str]:
    """Return whether a domain is up-to-date for a given IP address type."""
    uptodate = False
    dns_address = _query_dns_address(domain['domain'], ip_type)
    external_address = _lookup_public_address(ip_type)
    if dns_address == external_address and dns_address is not None:
        logger.info('Dynamic domain %s is up-to-date: %s (%s)',
                    domain['domain'], dns_address, ip_type)
        uptodate = True

    return uptodate, dns_address, external_address


def _update_dns_for_domain(domain: dict[str, Any], ip_type: Literal['ipv4',
                                                                    'ipv6'],
                           dns_address: str | None,
                           external_address: str) -> str | None:
    """Update DNS records for a single domain."""
    logger.info(
        'Updating dynamic domain %s, DNS address %s, looked up '
        'external address %s', domain['domain'], dns_address, external_address)
    if domain['service_type'] == 'gnudip':
        return gnudip.update(domain['server'], ip_type, domain['domain'],
                             domain['username'], domain['password'])
    else:
        return generic.update(domain, ip_type, external_address)


def _check_and_update_dns_for_domain(domain: dict[str, Any]):
    """Update DNS records for a single domain only when it is out-of-date."""
    result = True
    ip_addresses: list[str] = []
    error_code: str | None = None
    error_message: str | None = None

    ip_types: list[Literal['ipv4', 'ipv6']]
    if domain['ip_type'] == 'both':
        ip_types = ['ipv4', 'ipv6']
    else:
        ip_types = [domain['ip_type']]

    for ip_type in ip_types:
        try:
            uptodate, dns_address, external_address = \
                _check_uptodate_for_ip_type(domain, ip_type)

            ip_address = dns_address
            if not uptodate:
                ip_address = _update_dns_for_domain(domain, ip_type,
                                                    dns_address,
                                                    external_address)

            ip_addresses.append(ip_address)  # type: ignore
        except subprocess.CalledProcessError as exception:
            logger.exception('Failed to be update Dynamic DNS - %s', exception)
            result = False
            error_code = str(exception.__class__.__name__)
            error_message = f'Command failed: code={exception.returncode}, ' \
                f'stderr={exception.stderr.decode()}, ' \
                f'stdout={exception.stdout.decode()}'
        except Exception as exception:
            logger.exception('Failed to be update Dynamic DNS - %s', exception)
            result = False
            error_code = str(exception.__class__.__name__)
            error_message = str(exception.args[0])

    set_status(domain, result, ip_addresses, error_code, error_message)


def update_dns(_data) -> None:
    """For all configured domains, check and up to date DNS records."""
    config = get_config()
    app = app_module.App.get('dynamicdns')
    if not app.is_enabled():
        return

    # Update for each domain
    for domain in config['domains'].values():
        _check_and_update_dns_for_domain(domain)


def get_status() -> dict[str, Any]:
    """Return the status of recent update for each domain."""
    status = kvstore.get_default('dynamicdns_status', '{}')
    status = json.loads(status)
    status.setdefault('domains', {})

    domains = get_config()['domains']
    for domain in domains:
        if domain not in status['domains']:
            # No status available for newly configured domain
            status['domains'][domain] = {
                'domain': domain,
                'result': False,
                'ip_addresses': [],
                'error_code': None,
                'error_message': None,
                'timestamp': 0,
            }

    for domain_name, domain in status['domains'].items():
        domain.setdefault('ip_addresses', [])
        if 'ip_address' in domain:
            if domain['ip_address']:
                domain['ip_addresses'].append(domain['ip_address'])

            del domain['ip_address']

    return status


def set_status(domain: dict[str, Any], result: bool, ip_addresses: list[str],
               error_code: str | None, error_message: str | None):
    """Set the status of most recent update."""
    status = kvstore.get_default('dynamicdns_status', '{}')
    status = json.loads(status)
    domains = status.setdefault('domains', {})
    domains[domain['domain']] = {
        'domain': domain['domain'],
        'result': result,
        'ip_addresses': ip_addresses,
        'error_code': error_code,
        'error_message': error_message,
        'timestamp': int(time.time()),
    }
    kvstore.set('dynamicdns_status', json.dumps(status))


def get_config() -> dict[str, Any]:
    """Return the current configuration."""
    default_config: dict[str, Any] = {'domains': {}}
    config = kvstore.get_default('dynamicdns_config', '{}')
    config = json.loads(config) or default_config
    return _migrate_old_config(config)


def _migrate_old_config(config: dict[str, Any]) -> dict[str, Any]:
    """Upgrade the old configuration to newer format."""
    updated = False

    # Fix malformed configuration result of bug in older version.
    if 'null' in config['domains']:
        del config['domains']['null']
        updated = True

    # Upgrade from 'use_ipv6' to 'ip_type' key in domain configuration.
    for domain_name, domain in config['domains'].items():
        if 'use_ipv6' in domain:
            domain['ip_type'] = 'ipv6' if domain['use_ipv6'] else 'ipv4'
            del domain['use_ipv6']
            updated = True

    if updated:
        set_config(config)

    return config


def set_config(config: dict[str, Any]):
    """Set a new configuration."""
    kvstore.set('dynamicdns_config', json.dumps(config))


def notify_domain_added(domain_name: str):
    """Send a signal that domain has been added."""
    if app_module.App.get('dynamicdns').is_enabled():
        domain_added.send_robust(sender='dynamicdns',
                                 domain_type='domain-type-dynamic',
                                 name=domain_name, services='__all__')


def notify_domain_removed(domain_name: str):
    """Send a signal that domain has been removed."""
    if app_module.App.get('dynamicdns').is_enabled():
        domain_removed.send_robust(sender='dynamicdns',
                                   domain_type='domain-type-dynamic',
                                   name=domain_name)
