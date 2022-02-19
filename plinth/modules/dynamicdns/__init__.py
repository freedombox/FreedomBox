# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure ez-ipupdate client.
"""

import json
import logging
import subprocess
import time
import urllib

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, glib, kvstore, menu
from plinth.modules.backups.components import BackupRestore
from plinth.modules.names.components import DomainType
from plinth.modules.users.components import UsersAndGroups
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import gnudip, manifest

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
      'target=\'_blank\'>ddns.freedombox.org</a> or you may find free update '
      'URL based services at <a href=\'http://freedns.afraid.org/\' '
      'target=\'_blank\'>freedns.afraid.org</a>.'),
]

app = None


class DynamicDNSApp(app_module.App):
    """FreedomBox app for Dynamic DNS."""

    app_id = 'dynamicdns'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, depends=['names'],
                               name=_('Dynamic DNS Client'), icon='fa-refresh',
                               description=_description,
                               manual_page='DynamicDNS')
        self.add(info)

        menu_item = menu.Menu('menu-dynamicdns', info.name, None, info.icon,
                              'dynamicdns:index', parent_url_name='system')
        self.add(menu_item)

        enable_state = app_module.EnableState('enable-state-dynamicdns')
        self.add(enable_state)

        domain_type = DomainType('domain-type-dynamic',
                                 _('Dynamic Domain Name'), 'dynamicdns:index',
                                 can_have_certificate=True)
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

        # Check every 5 minutes (every 3 minutes in debug mode) to perform
        # dynamic DNS updates.
        interval = 180 if cfg.develop else 300
        glib.schedule(interval, update_dns)


def setup(helper, old_version=None):
    """Install and configure the module."""
    app.setup(old_version)
    if not old_version:
        helper.call('post', app.enable)

    if old_version == 1:
        config = actions.superuser_run('dynamicdns', ['export-config'])
        config = json.loads(config)
        if config['enabled']:
            app.enable()
        else:
            app.disable()

        del config['enabled']
        set_config(config)
        actions.superuser_run('dynamicdns', ['clean'])


def _query_external_address(domain):
    """Return the IP address by querying an external server."""
    if not domain['ip_lookup_url']:
        return None

    ip_option = '-6' if domain['use_ipv6'] else '-4'
    try:
        ip_address = subprocess.check_output([
            'wget', ip_option, '-o', '/dev/null', '-t', '3', '-T', '3', '-O',
            '-', domain['ip_lookup_url']
        ])
        return ip_address.decode().strip().lower()
    except subprocess.CalledProcessError as exception:
        logger.warning('Unable to lookup external IP with URL %s: %s',
                       domain['ip_lookup_url'], exception)
        return None


def _query_dns_address(domain):
    """Return the IP address in the DNS records."""
    ip_option = 'AAAA' if domain['use_ipv6'] else 'A'
    try:
        output = subprocess.check_output(
            ['host', '-t', ip_option, domain['domain']])
        return output.decode().split(' ')[-1].strip().lower()
    except subprocess.CalledProcessError as exception:
        logger.warning('Unable to lookup DNS for host %s: %s',
                       domain['domain'], exception)
        return None


def _update_using_url(domain, external_address):
    """Update DNS entry using an update URL."""
    update_url = domain['update_url']
    quote = urllib.parse.quote
    if external_address:
        update_url = update_url.replace('<Ip>', quote(external_address))

    if domain['domain']:
        update_url = update_url.replace('<Domain>', quote(domain['domain']))

    if domain['username']:
        update_url = update_url.replace('<User>', quote(domain['username']))

    if domain['password']:
        update_url = update_url.replace('<Pass>', quote(domain['password']))

    options = ['-o', '/dev/null', '-t', '3', '-T', '3']
    if domain['use_http_basic_auth']:
        options += [
            '--user', domain['username'], '--password', domain['password']
        ]

    if domain['disable_ssl_cert_check']:
        options += ['--no-check-certificate']

    if domain['use_ipv6']:
        options += ['-6']
    else:
        options += ['-4']

    command = ['wget', '-O', '/dev/null'] + options + [update_url]
    process = subprocess.run(command, check=False)
    return process.returncode == 0, external_address


def _update_dns_for_domain(domain):
    """Update DNS records for a single domain."""
    result = False
    ip_address = None
    error = None

    try:
        dns_address = _query_dns_address(domain)
        external_address = _query_external_address(domain)
        if dns_address == external_address and dns_address is not None:
            logger.info('Dynamic domain %s is up-to-date: %s',
                        domain['domain'], dns_address)
            result = True
            ip_address = dns_address
            error = ValueError('up-to-date')
        else:
            logger.info(
                'Updating dynamic domain %s, DNS address %s, looked up '
                'external address %s', domain['domain'], dns_address,
                external_address)
            if domain['service_type'] == 'gnudip':
                result, ip_address = gnudip.update(domain['server'],
                                                   domain['domain'],
                                                   domain['username'],
                                                   domain['password'])
            else:
                result, ip_address = _update_using_url(domain,
                                                       external_address)
    except Exception as exception:
        logger.exception('Failed to be update Dynamic DNS - %s', exception)
        error = exception

    set_status(domain, result, ip_address, error)


def update_dns(_data):
    """For all configured domains, check and up to date DNS records."""
    config = get_config()
    if not app.is_enabled():
        return

    # Update for each domain
    for domain in config['domains'].values():
        _update_dns_for_domain(domain)


def get_status():
    """Return the status of recent update for each domain."""
    status = kvstore.get_default('dynamicdns_status', '{}')
    status = json.loads(status)
    status.setdefault('domains', {})
    return status


def set_status(domain, result, ip_address, error=None):
    """Set the status of most recent update."""
    status = kvstore.get_default('dynamicdns_status', '{}')
    status = json.loads(status)
    domains = status.setdefault('domains', {})
    domains[domain['domain']] = {
        'domain': domain['domain'],
        'result': result,
        'ip_address': ip_address,
        'error_code': error.__class__.__name__ if error else None,
        'error_message': error.args[0] if error and error.args else None,
        'timestamp': int(time.time()),
    }
    kvstore.set('dynamicdns_status', json.dumps(status))


def get_config():
    """Return the current configuration."""
    default_config = {'domains': {}}
    config = kvstore.get_default('dynamicdns_config', '{}')
    return json.loads(config) or default_config


def set_config(config):
    """Set a new configuration."""
    kvstore.set('dynamicdns_config', json.dumps(config))


def notify_domain_added(domain_name):
    """Send a signal that domain has been added."""
    domain_added.send_robust(sender='dynamicdns',
                             domain_type='domain-type-dynamic',
                             name=domain_name, services='__all__')


def notify_domain_removed(domain_name):
    """Send a signal that domain has been removed."""
    domain_removed.send_robust(sender='dynamicdns',
                               domain_type='domain-type-dynamic',
                               name=domain_name)
