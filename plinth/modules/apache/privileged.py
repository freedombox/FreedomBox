# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Apache web server."""

import glob
import os
import pathlib
import re
import subprocess

from plinth import action_utils
from plinth.actions import privileged


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
        subprocess.run([
            'make-ssl-cert', 'generate-default-snakeoil', '--force-overwrite'
        ], check=True)
    # In case the certificate has been removed after ssl-cert is installed
    # on a fresh Debian machine.
    elif not os.path.exists('/etc/ssl/certs/ssl-cert-snakeoil.pem'):
        subprocess.run(['make-ssl-cert', 'generate-default-snakeoil'],
                       check=True)

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
        webserver.enable('authnz_ldap', kind='module')
        webserver.enable('auth_pubtkt', kind='module')

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

        # setup freedombox site
        webserver.enable('freedombox', kind='config')
        webserver.enable('freedombox-tls', kind='config')

        # enable serving Debian javascript libraries
        webserver.enable('javascript-common', kind='config')

        # default sites
        webserver.disable('000-default', kind='site')
        webserver.disable('default-tls', kind='site')
        webserver.disable('default-ssl', kind='site')
        webserver.disable('plinth', kind='site')
        webserver.disable('plinth-ssl', kind='site')
        webserver.enable('freedombox-default', kind='site')


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
def uwsgi_enable(name: str):
    """Enable uWSGI configuration and reload."""
    action_utils.uwsgi_enable(name)


@privileged
def uwsgi_disable(name: str):
    """Disable uWSGI configuration and reload."""
    action_utils.uwsgi_disable(name)
