# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Apache web server."""

import glob
import json
import os
import pathlib
import re
import shutil
import urllib.parse

import augeas

from plinth import action_utils, utils
from plinth.actions import privileged, secret_str

openidc_config_path = pathlib.Path(
    '/etc/apache2/conf-available/freedombox-openidc.conf')
metadata_dir_path = pathlib.Path(
    '/var/cache/apache2/mod_auth_openidc/metadata/')


def _get_sort_key_of_version(version):
    """Return the sort key for a given version string.

    Simple implementation hoping that PHP Apache module version numbers will be
    simple.

    """
    parts = []
    for part in version.split('.'):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(part)

    return parts


def _sort_versions(versions):
    """Return a list of sorted version strings."""
    return sorted(versions, key=_get_sort_key_of_version, reverse=True)


def _disable_mod_php(webserver):
    """Disable all mod_php versions.

    Idempotent and harmless if all or no PHP modules are identified.
    Problematic if only some modules are found.

    """
    paths = glob.glob('/etc/apache2/mods-available/php*.conf')
    versions = []
    for path in paths:
        match = re.search(r'\/php(.*)\.conf$', path)
        if match:
            versions.append(match[1])

    versions = _sort_versions(versions)

    for version in versions:
        webserver.disable('php' + version, kind='module')


@privileged
def setup(old_version: int):
    """Setup Apache configuration."""
    # Regenerate the snakeoil self-signed SSL certificate. This is so that
    # FreedomBox images don't all have the same certificate. When FreedomBox
    # package is installed via apt, don't regenerate. When upgrading to newer
    # version of Apache FreedomBox app and setting up for the first time don't
    # regenerate.
    if action_utils.is_disk_image() and old_version == 0:
        action_utils.run([
            'make-ssl-cert', 'generate-default-snakeoil', '--force-overwrite'
        ], check=True)
    # In case the certificate has been removed after ssl-cert is installed
    # on a fresh Debian machine.
    elif not os.path.exists('/etc/ssl/certs/ssl-cert-snakeoil.pem'):
        action_utils.run(['make-ssl-cert', 'generate-default-snakeoil'],
                         check=True)

    _setup_oidc_config()

    with action_utils.WebserverChange() as webserver:
        # Disable mod_php as we have switched to mod_fcgi + php-fpm. Disable
        # before switching away from mpm_prefork otherwise switching fails due
        # dependency.
        _disable_mod_php(webserver)

        # set the prefork worker model
        webserver.disable('mpm_worker', kind='module')
        webserver.disable('mpm_prefork', kind='module')
        webserver.enable('mpm_event', kind='module')

        # enable miscellaneous modules.
        webserver.enable('proxy', kind='module')
        webserver.enable('proxy_http', kind='module')
        webserver.enable('proxy_fcgi', kind='module')
        webserver.enable('proxy_html', kind='module')
        webserver.enable('rewrite', kind='module')
        webserver.enable('macro', kind='module')
        webserver.enable('expires', kind='module')

        # Disable logging into files, use FreedomBox configured systemd logging
        webserver.disable('other-vhosts-access-log', kind='config')

        # Disable /server-status page to avoid leaking private info.
        webserver.disable('status', kind='module')

        # Enable HTTP/2 protocol
        webserver.enable('http2', kind='module')

        # Enable shared object cache needed for OSCP stapling. Needed by
        # mod_ssl.
        webserver.enable('socache_shmcb', kind='module')

        # switch to mod_ssl from mod_gnutls
        webserver.disable('gnutls', kind='module')
        webserver.enable('ssl', kind='module')

        # enable mod_alias for RedirectMatch
        webserver.enable('alias', kind='module')

        # enable mod_headers for HSTS
        webserver.enable('headers', kind='module')

        # Various modules for authentication/authorization
        webserver.enable('auth_openidc', kind='module')
        webserver.enable('authnz_ldap', kind='module')
        webserver.disable('auth_pubtkt', kind='module')

        # enable some critical modules to avoid restart while installing
        # FreedomBox applications.
        webserver.disable('cgi', kind='module')  # For process MPMs
        webserver.enable('cgid', kind='module')  # For threaded MPMs
        webserver.enable('proxy_uwsgi', kind='module')
        webserver.enable('proxy_wstunnel', kind='module')

        # enable configuration for PHP-FPM
        webserver.enable('php-fpm-freedombox', kind='config')

        # enable users to share files uploaded to ~/public_html
        webserver.enable('userdir', kind='module')

        # enable WebDAV protocol. Used by feather wiki and potentially by other
        # apps and file sharing.
        webserver.enable('dav', kind='module')
        webserver.enable('dav_fs', kind='module')

        # setup freedombox configuration
        webserver.enable('10-freedombox', kind='config')
        webserver.enable('freedombox', kind='config')
        webserver.enable('freedombox-tls', kind='config')
        webserver.enable('freedombox-openidc.conf', kind='config')

        # enable serving Debian javascript libraries
        webserver.enable('javascript-common', kind='config')

        # default sites
        webserver.disable('000-default', kind='site')
        webserver.disable('default-tls', kind='site')
        webserver.disable('default-ssl', kind='site')
        webserver.disable('plinth', kind='site')
        webserver.disable('plinth-ssl', kind='site')
        webserver.enable('freedombox-default', kind='site')


def _load_augeas():
    """Initialize augeas for this app's configuration file."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Httpd', str(openidc_config_path))
    aug.set('/augeas/context', '/files' + str(openidc_config_path))
    aug.load()

    return aug


def _get_mod_openidc_passphrase() -> str:
    """Read existing mod-auth-openidc passphase.

    Instead of generating a new passphrase every time, use existing one. If the
    passphrase changes, all the existing sessions will be logged out and users
    will have login to apps again.
    """
    aug = _load_augeas()
    for directive in aug.match('*/directive'):
        if aug.get(directive) == 'OIDCCryptoPassphrase':
            return aug.get(directive + '/arg')

    # Does not exist already, generate new
    return utils.generate_password(size=64)


@privileged
def setup_oidc_client(netloc: str, client_id: str, client_secret: secret_str):
    """Setup client ID and secret for provided domain.

    netloc is hostname or IP address along with port as parsed by
    urllib.parse.urlparse() method from a URL.
    """
    issuer = f'{netloc}/freedombox/o'
    issuer_quoted = urllib.parse.quote_plus(issuer)
    client_path = metadata_dir_path / f'{issuer_quoted}.client'
    if client_path.exists():
        try:
            current_data = json.loads(client_path.read_text())
            if (current_data['client_id'] == client_id
                    and current_data['client_secret'] == client_secret):
                return
        except Exception:
            pass

    client_configuration = {
        'client_id': client_id,
        'client_secret': client_secret
    }
    previous_umask = os.umask(0o077)
    try:
        client_path.write_text(json.dumps(client_configuration))
    finally:
        os.umask(previous_umask)

    shutil.chown(client_path, 'www-data', 'www-data')


def _setup_oidc_config():
    """Setup Apache as a OpenID Connect Relying Party.

    Ensure that auth_openidc module's metadata directory is created. It will be
    used to store provider-specific configuration. Since FreedomBox will be
    configured with multiple domains and some of them may not be accessible due
    to the access method, we need to configure a separate IDP for each domain.
    This is also because auth_openidc does not allow IDP configuration with
    relative URLs.

    Keep the metadata directory and configuration file unreadable by non-admin
    users since they contain module's crypto secret and OIDC client secret.

    # Session management

    When apps like Syncthing are protected with mod_auth_openidc, there a
    session maintained using server-side session storage and a cookie on the
    client side. This session is different from the session managed by the
    OpenID Connect Provider (FreedomBox web interface). As long as this session
    is valid, no further authentication mechanisms are triggered.

    When the session expires, if the request is a GET request (due to page
    reload), the browser is redirected to OP, a fresh token is created, and the
    page is loaded. However, for POST requests, 401 error is returned and if
    the application is unaware, it won't do much about it. So, this
    necessitates keeping the session timeout value high.

    When logout is performed on FreedomBox web interface, mod_auth_openidc
    cookie is also removed and logout feels instantaneous. However, this won't
    work for applications not using mod_auth_openidc and for applications
    hosted on other domains. A better way to do this is to implement OpenID
    Connect's Back-Channel Logout or using OpenID Connect Session Management.

    For more about session management see:
    https://github.com/OpenIDC/mod_auth_openidc/wiki/Sessions-and-Timeouts and
    https://github.com/OpenIDC/mod_auth_openidc/wiki/Session-Management-Settings
    """
    metadata_dir_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    metadata_dir_path.mkdir(mode=0o700, exist_ok=True)
    shutil.chown(metadata_dir_path.parent, 'www-data', 'www-data')
    shutil.chown(metadata_dir_path, 'www-data', 'www-data')

    # XXX: Default cache type is 'shm' or shared memory. This is lost when
    # Apache is restarted and users/apps will have to reauthenticate. Improve
    # this by using file (in tmpfs), redis, or memache caches.

    passphrase = _get_mod_openidc_passphrase()
    configuration = f'''##
## OpenID Connect related configuration
##
<IfModule mod_auth_openidc.c>
    OIDCCryptoPassphrase {passphrase}
    OIDCMetadataDir {str(metadata_dir_path)}
    # Use relative URL to redirect to the same origin as the resource
    OIDCDiscoverURL /freedombox/apache/discover-idp/
    OIDCSSLValidateServer Off
    OIDCProviderMetadataRefreshInterval 86400

    # Expire the mod_auth_openidc session (not the OpenID Conneect Provider
    # session) after 10 hours of idle with a maximum session duration equal to
    # the expiry time of the ID token (10 hours). This allows applications such
    # as FeatherWiki to have long editing sessions before save.
    OIDCSessionInactivityTimeout 36000
    OIDCSessionMaxDuration 0

    # Use relative URL to return to the original domain
    OIDCRedirectURI /apache/oidc/callback
    OIDCRemoteUserClaim sub

    # The redirect URI must always be under a location protected by
    # mod_openidc.
    <Location /apache>
        AuthType openid-connect
        # Checking audience is not necessary, but we need to check some claim.
        Require claim aud:apache
    </Location>
</IfModule>
'''
    previous_umask = os.umask(0o077)
    try:
        openidc_config_path.write_text(configuration)
    finally:
        os.umask(previous_umask)


# TODO: Check that the (name, kind) is a managed by FreedomBox before
# performing operation.
@privileged
def enable(name: str, kind: str):
    """Enable an Apache site/config/module."""
    _assert_kind(kind)
    action_utils.webserver_enable(name, kind)


@privileged
def disable(name: str, kind: str):
    """Disable an Apache site/config/module."""
    _assert_kind(kind)
    action_utils.webserver_disable(name, kind)


def _assert_kind(kind: str):
    """Raise and exception if kind parameter has an unexpected value."""
    if kind not in ('site', 'config', 'module'):
        raise ValueError('Invalid value for parameter kind')


@privileged
def link_root(domain: str, name: str):
    """Link the Apache site root configuration to app configuration."""
    if '/' in domain or '/' in name:
        raise ValueError('Invalid domain or name')

    target_config = f'{name}.conf'

    include_root = pathlib.Path('/etc/apache2/includes/')
    config = include_root / f'{domain}-include-freedombox.conf'
    config.unlink(missing_ok=True)
    config.symlink_to(target_config)
    action_utils.service_reload('apache2')


@privileged
def unlink_root(domain: str):
    """Unlink the Apache site root configuration from app configuration."""
    if '/' in domain:
        raise ValueError('Invalid domain')

    include_root = pathlib.Path('/etc/apache2/includes/')
    config = include_root / f'{domain}-include-freedombox.conf'
    if not config.is_symlink():
        return  # Does not exist or not a symlink

    config.unlink()
    action_utils.service_reload('apache2')


@privileged
def domain_setup(domain: str):
    """Add site specific configuration for a domain."""
    if '/' in domain:
        raise ValueError('Invalid domain')

    path = pathlib.Path('/etc/apache2/sites-available/')
    path = path / (domain + '.conf')
    configuration = 'Use FreedomBoxTLSSiteMacro {domain}\n'
    if path.is_file():
        return  # File already exists. Assume it to be correct one.

    path.write_text(configuration.format(domain=domain))

    with action_utils.WebserverChange() as webserver:
        webserver.enable('freedombox-tls-site-macro', kind='config')
        webserver.enable(domain, kind='site')


@privileged
def domain_remove(domain: str):
    """Remove site specific configuration for a domain."""
    if '/' in domain:
        raise ValueError('Invalid domain')

    with action_utils.WebserverChange() as webserver:
        webserver.disable(domain, kind='site')

    path = pathlib.Path('/etc/apache2/sites-available/')
    path = path / (domain + '.conf')
    path.unlink(missing_ok=True)
