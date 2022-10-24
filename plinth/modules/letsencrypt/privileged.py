# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Let's Encrypt."""

import filecmp
import glob
import importlib
import inspect
import os
import pathlib
import re
import shutil
import subprocess
import sys
from typing import Any

import configobj

from plinth import action_utils
from plinth import app as app_module
from plinth import cfg
from plinth.actions import privileged
from plinth.modules import letsencrypt as le

TEST_MODE = False
LE_DIRECTORY = '/etc/letsencrypt/'
ETC_SSL_DIRECTORY = '/etc/ssl/'
RENEWAL_DIRECTORY = '/etc/letsencrypt/renewal/'
AUTHENTICATOR = 'webroot'
WEB_ROOT_PATH = '/var/www/html'
APACHE_PREFIX = '/etc/apache2/sites-available/'
APACHE_CONFIGURATION = '''
Use FreedomBoxTLSSiteMacro {domain}
'''


def _get_certificate_expiry(domain: str) -> str:
    """Return the expiry date of a certificate."""
    certificate_file = os.path.join(le.LIVE_DIRECTORY, domain, 'cert.pem')
    output = subprocess.check_output(
        ['openssl', 'x509', '-enddate', '-noout', '-in', certificate_file])
    return output.decode().strip().split('=')[1]


def _get_modified_time(domain: str) -> int:
    """Return the last modified time of a certificate."""
    certificate_file = pathlib.Path(le.LIVE_DIRECTORY) / domain / 'cert.pem'
    return int(certificate_file.stat().st_mtime)


def _get_validity_status(domain: str) -> str:
    """Return validity status of a certificate; valid, revoked, expired."""
    output = subprocess.check_output(['certbot', 'certificates', '-d', domain])
    line = output.decode(sys.stdout.encoding)

    match = re.search(r'INVALID: (.*)\)', line)
    if match is not None:
        validity = match.group(1).lower()
    elif re.search('VALID', line) is not None:
        validity = 'valid'
    else:
        validity = 'unknown'

    return validity


def _get_status() -> dict[str, Any]:
    """Return Python dictionary of currently configured domains.

    Should be run as root, otherwise might yield a wrong, empty answer.
    """
    try:
        domains = os.listdir(le.LIVE_DIRECTORY)
    except OSError:
        domains = []

    domains = [
        domain for domain in domains
        if os.path.isdir(os.path.join(le.LIVE_DIRECTORY, domain))
    ]

    domain_status = {}
    for domain in domains:
        domain_status[domain] = {
            'certificate_available':
                True,
            'expiry_date':
                _get_certificate_expiry(domain),
            'web_enabled':
                action_utils.webserver_is_enabled(domain, kind='site'),
            'validity':
                _get_validity_status(domain),
            'lineage':
                str(pathlib.Path(le.LIVE_DIRECTORY) / domain),
            'modified_time':
                _get_modified_time(domain)
        }
    return domain_status


@privileged
def setup(old_version: int):
    """Upgrade old site configuration to new macro based style.

    Nothing to do for first time setup and for newer versions.
    """
    if old_version == 2:
        _remove_old_hooks()
        return

    if old_version != 1:
        return

    domain_status = _get_status()
    with action_utils.WebserverChange() as webserver_change:
        for domain in domain_status:
            _setup_webserver_config(domain, webserver_change)


@privileged
def get_status() -> dict[str, Any]:
    """Return a dictionary of currently configured domains."""
    domain_status = _get_status()
    return {'domains': domain_status}


@privileged
def get_modified_time(domain: str) -> int:
    """Return the modified time of a certificate as integer."""
    return _get_modified_time(domain)


@privileged
def revoke(domain: str):
    """Disable a domain and revoke the certificate."""
    cert_path = pathlib.Path(le.LIVE_DIRECTORY) / domain / 'cert.pem'
    if cert_path.exists():
        command = [
            'certbot', 'revoke', '--non-interactive', '--domain', domain,
            '--cert-path',
            str(cert_path)
        ]
        if TEST_MODE:
            command.append('--staging')

        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        _, stderr = process.communicate()
        if process.returncode:
            raise RuntimeError('Error revoking certificate: {error}'.format(
                error=stderr.decode()))

    action_utils.webserver_disable(domain, kind='site')


@privileged
def obtain(domain: str):
    """Obtain a certificate for a domain and setup website."""
    command = [
        'certbot', 'certonly', '--non-interactive', '--text', '--agree-tos',
        '--register-unsafely-without-email', '--domain', domain,
        '--authenticator', AUTHENTICATOR, '--webroot-path', WEB_ROOT_PATH,
        '--renew-by-default'
    ]
    if TEST_MODE:
        command.append('--staging')

    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    if process.returncode:
        raise RuntimeError('Error obtaining certificate: {error}'.format(
            error=stderr.decode()))

    with action_utils.WebserverChange() as webserver_change:
        _setup_webserver_config(domain, webserver_change)


def _remove_old_hooks():
    """Remove old style renewal hooks from individual configuration files.

    This has been replaced with global hooks by adding script files in
    directory /etc/letsencrypt/renewal-hooks/{pre,post,deploy}/.
    """
    for file_path in glob.glob(RENEWAL_DIRECTORY + '*.conf'):
        try:
            _remove_old_hooks_from_file(file_path)
        except Exception as exception:
            print('Error removing hooks from file:', file_path, exception)


def _remove_old_hooks_from_file(file_path: str):
    """Remove old style hooks from a single configuration file."""
    config = configobj.ConfigObj(file_path)
    edited = False
    for line in config.initial_comment:
        if 'edited by plinth' in line.lower():
            edited = True

    if not edited:
        return

    config.initial_comment = [
        line for line in config.initial_comment
        if 'edited by plinth' not in line.lower()
    ]

    if 'pre_hook' in config['renewalparams']:
        del config['renewalparams']['pre_hook']

    if 'renew_hook' in config['renewalparams']:
        del config['renewalparams']['renew_hook']

    if 'post_hook' in config['renewalparams']:
        del config['renewalparams']['post_hook']

    config.write()


@privileged
def copy_certificate(managing_app: str, source_private_key: str,
                     source_certificate: str, private_key: str,
                     certificate: str, user_owner: str, group_owner: str):
    """Copy certificate from LE directory to daemon's directory.

    Set ownership and permissions as requested needed by the daemon.

    """
    source_private_key_path = pathlib.Path(source_private_key).resolve()
    _assert_source_directory(source_private_key_path)
    source_certificate_path = pathlib.Path(source_certificate).resolve()
    _assert_source_directory(source_certificate_path)

    private_key_path = pathlib.Path(private_key).resolve()
    _assert_managed_path(managing_app, private_key_path)
    certificate_path = pathlib.Path(certificate).resolve()
    _assert_managed_path(managing_app, certificate_path)

    # Create directories, owned by root
    private_key_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    certificate_path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)

    # Private key is only accessible to the user owner
    old_mask = os.umask(0o177)
    shutil.copyfile(source_private_key_path, private_key_path)

    if certificate_path != private_key_path:
        # Certificate is only writable by the user owner
        os.umask(0o133)
        shutil.copyfile(source_certificate_path, certificate_path)
    else:
        # If private key and certificate are the same file, append one after
        # the other.
        source_certificate_bytes = source_certificate_path.read_bytes()
        with private_key_path.open(mode='a+b') as file_handle:
            file_handle.write(source_certificate_bytes)

    os.umask(old_mask)

    shutil.chown(certificate_path, user=user_owner, group=group_owner)
    shutil.chown(private_key_path, user=user_owner, group=group_owner)


@privileged
def compare_certificate(managing_app: str, source_private_key: str,
                        source_certificate: str, private_key: str,
                        certificate: str) -> bool:
    """Compare LE certificate with an app certificate."""
    source_private_key_path = pathlib.Path(source_private_key)
    source_certificate_path = pathlib.Path(source_certificate)
    _assert_source_directory(source_private_key_path)
    _assert_source_directory(source_certificate_path)

    private_key_path = pathlib.Path(private_key)
    certificate_path = pathlib.Path(certificate)
    _assert_managed_path(managing_app, private_key_path)
    _assert_managed_path(managing_app, certificate_path)

    result = False
    try:
        if filecmp.cmp(source_certificate_path, certificate_path) and \
           filecmp.cmp(source_private_key_path, private_key_path):
            result = True
    except FileNotFoundError:
        result = False

    return result


def _assert_source_directory(path):
    """Assert that a path is a valid source of a certificates."""
    assert (str(path).startswith(LE_DIRECTORY)
            or str(path).startswith(ETC_SSL_DIRECTORY))


def _get_managed_path(path):
    """Return the managed path given a certificate path."""
    if '{domain}' in path:
        return pathlib.Path(path.partition('{domain}')[0])

    return pathlib.Path(path).parent


def _assert_managed_path(module, path):
    """Check that path is in fact managed by module."""
    cfg.read()
    module_file = pathlib.Path(cfg.config_dir) / 'modules-enabled' / module
    module_path = module_file.read_text().strip()

    module = importlib.import_module(module_path)
    module_classes = inspect.getmembers(module, inspect.isclass)
    app_classes = [
        cls[1] for cls in module_classes if issubclass(cls[1], app_module.App)
    ]

    managed_paths = []
    for cls in app_classes:
        app = cls()
        from plinth.modules.letsencrypt.components import LetsEncrypt
        components = app.get_components_of_type(LetsEncrypt)
        for component in components:
            if component.private_key_path:
                managed_paths.append(
                    _get_managed_path(component.private_key_path))
            if component.certificate_path:
                managed_paths.append(
                    _get_managed_path(component.certificate_path))

    if not set(path.parents).intersection(set(managed_paths)):
        raise AssertionError('Not a managed path')


@privileged
def delete(domain: str):
    """Disable a domain and delete the certificate."""
    command = ['certbot', 'delete', '--non-interactive', '--cert-name', domain]
    process = subprocess.Popen(command, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    _, stderr = process.communicate()
    if process.returncode:
        raise RuntimeError('Error deleting certificate: {error}'.format(
            error=stderr.decode()))

    action_utils.webserver_disable(domain, kind='site')


def _setup_webserver_config(domain, webserver_change):
    """Create SSL web server configuration for a domain.

    Do so only if there is no configuration existing.
    """
    file_name = os.path.join(APACHE_PREFIX, domain + '.conf')
    if os.path.isfile(file_name):
        os.rename(file_name, file_name + '.fbx-bak')

    with open(file_name, 'w', encoding='utf-8') as file_handle:
        file_handle.write(APACHE_CONFIGURATION.format(domain=domain))

    webserver_change.enable('freedombox-tls-site-macro', kind='config')
    webserver_change.enable(domain, kind='site')
