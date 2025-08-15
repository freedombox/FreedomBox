# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for the ejabberd service."""

import logging
import os
import re
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML, scalarstring

from plinth import action_utils
from plinth.actions import privileged
from plinth.version import Version

logger = logging.getLogger(__name__)

EJABBERD_CONFIG = '/etc/ejabberd/ejabberd.yml'
EJABBERD_BACKUP = '/var/log/ejabberd/ejabberd.dump'
EJABBERD_BACKUP_NEW = '/var/log/ejabberd/ejabberd_new.dump'
EJABBERD_ORIG_CERT = '/etc/ejabberd/ejabberd.pem'
EJABBERD_MANAGED_COTURN = '/etc/ejabberd/freedombox_managed_coturn'
IQDISC_DEPRECATED_VERSION = Version('18.03')
MOD_IRC_DEPRECATED_VERSION = Version('18.06')

yaml = YAML()
yaml.allow_duplicate_keys = True
yaml.preserve_quotes = True  # type: ignore [assignment]

TURN_URI_REGEX = r'(stun|turn):(.*):([0-9]{4})(?:\?transport=(tcp|udp))?'


@privileged
def pre_install(domain_name: str):
    """Preseed debconf values before packages are installed."""
    if not domain_name:
        # If new domain_name is blank, use hostname instead.
        domain_name = socket.gethostname()

    action_utils.debconf_set_selections(
        ['ejabberd ejabberd/hostname string ' + domain_name])


@privileged
def setup(domain_name: str):
    """Enable LDAP authentication."""
    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    for listen_port in conf['listen']:
        if 'tls' in listen_port:
            listen_port['tls'] = False
        if 'use_turn' in listen_port:
            conf['listen'].remove(listen_port)  # Use coturn instead
        if listen_port['port'] == 5443:
            # Enable XEP-0363 HTTP File Upload
            listen_port['request_handlers']['/upload'] = 'mod_http_upload'

    origin_key = scalarstring.DoubleQuotedScalarString(
        'Access-Control-Allow-Origin')
    origin_value = scalarstring.DoubleQuotedScalarString('https://@HOST@')
    methods_key = scalarstring.DoubleQuotedScalarString(
        'Access-Control-Allow-Methods')
    methods_value = scalarstring.DoubleQuotedScalarString(
        'GET,HEAD,PUT,OPTIONS')
    headers_key = scalarstring.DoubleQuotedScalarString(
        'Access-Control-Allow-Headers')
    headers_value = scalarstring.DoubleQuotedScalarString('Content-Type')
    conf['modules']['mod_http_upload'] = {
        'put_url': 'https://@HOST@/upload',
        'custom_headers': {
            origin_key: origin_value,
            methods_key: methods_value,
            headers_key: headers_value,
        },
    }

    conf['auth_method'] = 'ldap'
    conf['ldap_servers'] = [scalarstring.DoubleQuotedScalarString('localhost')]
    conf['ldap_base'] = scalarstring.DoubleQuotedScalarString(
        'ou=users,dc=thisbox')

    with open(EJABBERD_CONFIG, 'w', encoding='utf-8') as file_handle:
        yaml.dump(conf, file_handle)

    _upgrade_config(domain_name)

    try:
        subprocess.check_output(['ejabberdctl', 'restart'])
    except subprocess.CalledProcessError as err:
        logger.warn('Failed to restart ejabberd with new configuration: %s',
                    err)


def _upgrade_config(domain):
    """Fix the config file by removing deprecated settings."""
    current_version = _get_version()
    if not current_version:
        logger.warn('Warning: Unable to get ejabberd version.')

    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    # Check if `iqdisc` is present and remove it
    if 'mod_mam' in conf['modules'] and \
       (not current_version or current_version > IQDISC_DEPRECATED_VERSION):
        conf['modules']['mod_mam'].pop('iqdisc', None)

    # check if mod_irc is present in modules and remove it
    if 'mod_irc' in conf['modules'] and \
       (not current_version or current_version > MOD_IRC_DEPRECATED_VERSION):
        conf['modules'].pop('mod_irc')

    # Debian has a patch to configuration to change port 5443 to 5280 in
    # ejabberd package version 18.12. However, 5443 is the correct port to host
    # BOSH. So, change it back. In 19.x, this behavior has changed to use both
    # ports 5443 (for BOSH) and 5280 (for web administration).
    bosh_port = any((True for listen_port in conf['listen']
                     if listen_port['port'] == 5443))
    if not bosh_port:
        for listen_port in conf['listen']:
            if listen_port['port'] == 5280:
                listen_port['port'] = 5443

    cert_dir = Path('/etc/ejabberd/letsencrypt') / domain
    cert_file = str(cert_dir / 'ejabberd.pem')
    cert_file = scalarstring.DoubleQuotedScalarString(cert_file)
    conf['s2s_certfile'] = cert_file
    for listen_port in conf['listen']:
        if 'certfile' in listen_port:
            listen_port['certfile'] = cert_file

    # Write changes back to the file
    with open(EJABBERD_CONFIG, 'w', encoding='utf-8') as file_handle:
        yaml.dump(conf, file_handle)


@privileged
def pre_change_hostname(old_hostname: str, new_hostname: str):
    """Prepare ejabberd for hostname change."""
    if not shutil.which('ejabberdctl'):
        logger.info('ejabberdctl not found')
        return

    action_utils.run(['ejabberdctl', 'backup', EJABBERD_BACKUP], check=False)
    subprocess.check_output([
        'ejabberdctl', 'mnesia-change-nodename', 'ejabberd@' + old_hostname,
        'ejabberd@' + new_hostname, EJABBERD_BACKUP, EJABBERD_BACKUP_NEW
    ])
    os.remove(EJABBERD_BACKUP)


@privileged
def change_hostname():
    """Update ejabberd with new hostname."""
    if not shutil.which('ejabberdctl'):
        return

    action_utils.service_stop('ejabberd')
    action_utils.run(['pkill', '-u', 'ejabberd'], check=False)

    # Make sure there aren't files in the Mnesia spool dir
    os.makedirs('/var/lib/ejabberd/oldfiles', exist_ok=True)
    action_utils.run('mv /var/lib/ejabberd/*.* /var/lib/ejabberd/oldfiles/',
                     shell=True, check=False)

    action_utils.service_start('ejabberd')

    # restore backup database
    if os.path.exists(EJABBERD_BACKUP_NEW):
        try:
            subprocess.check_output(
                ['ejabberdctl', 'restore', EJABBERD_BACKUP_NEW])
            os.remove(EJABBERD_BACKUP_NEW)
        except subprocess.CalledProcessError as err:
            logger.error('Failed to restore ejabberd backup database: %s', err)
    else:
        logger.error('Could not load ejabberd backup database: %s not found' %
                     EJABBERD_BACKUP_NEW)


@privileged
def get_domains() -> list[str]:
    """Get all configured domains."""
    if not shutil.which('ejabberdctl'):
        return []

    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    return conf['hosts']


@privileged
def add_domain(domain_name: str):
    """Update ejabberd with new domain name.

    Restarting ejabberd is handled by letsencrypt-ejabberd component.
    """
    if not shutil.which('ejabberdctl'):
        logger.info('ejabberdctl not found')
        return

    # Add updated domain name to ejabberd hosts list.
    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    conf['hosts'].append(scalarstring.DoubleQuotedScalarString(domain_name))

    conf['hosts'] = list(set(conf['hosts']))

    with open(EJABBERD_CONFIG, 'w', encoding='utf-8') as file_handle:
        yaml.dump(conf, file_handle)

    # Restarting ejabberd is handled by letsencrypt-ejabberd component.


@privileged
def set_domains(domains: list[str]):
    """Set list of ejabberd domains.

    Restarting ejabberd is handled by letsencrypt-ejabberd component.
    """
    if not len(domains):
        raise ValueError('No domains provided')

    if not shutil.which('ejabberdctl'):
        return

    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    conf['hosts'] = domains

    with open(EJABBERD_CONFIG, 'w', encoding='utf-8') as file_handle:
        yaml.dump(conf, file_handle)


@privileged
def mam(command: str) -> bool | None:
    """Enable, disable, or get status of Message Archive Management (MAM)."""
    if command not in ('enable', 'disable', 'status'):
        raise ValueError('Invalid command')

    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    if 'modules' not in conf:
        return None

    if command == 'status':
        return 'mod_mam' in conf['modules']

    if command == 'enable':
        # Explicitly set the recommended / default settings for mod_mam,
        # see https://docs.ejabberd.im/admin/configuration/#mod-mam.
        settings_mod_mam = {
            'mod_mam': {
                'db_type':
                    'mnesia',  # default is 'mnesia' (w/o set default_db)
                'default': 'always',  # helps various clients to use mam
                'request_activates_archiving': False,  # default False
                'assume_mam_usage': False,  # for non-ack'd msgs, default False
                'cache_size': 1000,  # default is 1000 items
                'cache_life_time': 3600  # default is 3600 seconds = 1h
            }
        }
        conf['modules'].update(settings_mod_mam)
    elif command == 'disable':
        # disable modules by erasing from config file
        if 'mod_mam' in conf['modules']:
            conf['modules'].pop('mod_mam')

    with open(EJABBERD_CONFIG, 'w', encoding='utf-8') as file_handle:
        yaml.dump(conf, file_handle)

    if action_utils.service_is_running('ejabberd'):
        action_utils.run(['ejabberdctl', 'reload_config'], check=False)

    return None


def _generate_service(uri: str) -> dict:
    """Generate ejabberd mod_stun_disco service config from Coturn URI."""
    pattern = re.compile(TURN_URI_REGEX)
    match = pattern.match(uri)
    if not match:
        raise ValueError('URL does not match TURN URI')

    typ, domain, port, transport = match.groups('udp')
    return {
        "host": domain,
        "port": int(port),
        "type": typ,
        "transport": transport,
    }


def _generate_uris(services: list[dict]) -> list[str]:
    """Generate STUN/TURN URIs from ejabberd mod_stun_disco service config."""
    uris = []
    for s in services:
        uri = f"{s['type']}:{s['host']}:{s['port']}"
        if s['type'] != 'stun':
            uri += f"?transport={s['transport']}"

        if uri not in uris:
            uris.append(uri)

    return uris


@privileged
def get_turn_config() -> tuple[dict[str, Any], bool]:
    """Get the latest STUN/TURN configuration in JSON format."""
    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    mod_stun_disco_config = conf['modules']['mod_stun_disco']
    managed = os.path.exists(EJABBERD_MANAGED_COTURN)

    if bool(mod_stun_disco_config):
        return {
            'domain': '',
            'uris': _generate_uris(mod_stun_disco_config['services']),
            'shared_secret': mod_stun_disco_config['secret'],
        }, managed
    else:
        return {'domain': None, 'uris': [], 'shared_secret': None}, managed


@privileged
def configure_turn(turn_server_config: dict[str, Any], managed: bool):
    """Set parameters for the STUN/TURN server to use with ejabberd."""
    uris = turn_server_config['uris']
    mod_stun_disco_config = {}

    if turn_server_config['uris'] and turn_server_config['shared_secret']:
        mod_stun_disco_config = {
            'credentials_lifetime': '1000d',
            'secret': turn_server_config['shared_secret'],
            'services': [_generate_service(uri) for uri in uris]
        }

    with open(EJABBERD_CONFIG, 'r', encoding='utf-8') as file_handle:
        conf = yaml.load(file_handle)

    conf['modules']['mod_stun_disco'] = mod_stun_disco_config

    with open(EJABBERD_CONFIG, 'w', encoding='utf-8') as file_handle:
        yaml.dump(conf, file_handle)

    if managed:
        Path(EJABBERD_MANAGED_COTURN).touch()
    else:
        Path(EJABBERD_MANAGED_COTURN).unlink(missing_ok=True)

    if action_utils.service_is_running('ejabberd'):
        action_utils.run(['ejabberdctl', 'reload_config'], check=False)


def _get_version():
    """Get the current ejabberd version."""
    try:
        output = subprocess.check_output(['ejabberdctl',
                                          'status']).decode('utf-8')
    except subprocess.CalledProcessError:
        return None

    version_info = output.strip().split('\n')[-1].split()
    if version_info:
        version = str(version_info[1])
        return Version(version)
    return None
