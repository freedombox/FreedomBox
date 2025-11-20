# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for Apache server.

This module implements a mechanism for protecting various URL paths using
FreedomBox's OpenID Connect implementation as Identity Provider and
mod_auth_oidc as Relying Party. The following is a simplified description of
how the flow works:

- User accesses the URL /foo using a browser. /foo is a URL path which is
  protected by this module's OpenID Connect SSO (using AuthType
  openid-connect).

- mod_auth_opendic seizes control and checks for authorization. Since this is
  the first visit, it starts the authentication/authorization process. It first
  redirects the browser to provider discovery URL
  /freedombox/apache/discover-idp/.

- This URL selects and Identity Provider based on incoming URL's host header.
  It will select https://mydomain.example/freedombox/o as IDP if the original
  URL is https://mydomain.example/foo. Or https://freedombox.local/freedombox/o
  if the original URL is https://freedombox.local/foo. After selection it will
  redirect the browser back to /apache/oidc/callback with the selected IDP in
  the GET parameters.

- /apache/oidc/callback is controlled by mod_auth_openidc which receives the
  IDP selection. It will then query the IDP for further information such as
  authorization URL, token URL, supported scopes and claims. This is done using
  a backend call to /freedombox/o/.well-known/openid-configuration.

- After determining the authorization end point (/freedombox/o/authorize/) from
  the metadata, mod_auth_openidc will start the authentication/authorization
  process by redirecting the browser to the URL.

- FreedomBox shows login page if the user is not already logged in. User logs
  in.

- FreedomBox will show a page asking the user to authorize the application to
  access information such as name and email. In case of Apache's
  mod_auth_openidc, this is skipped.

- FreedomBox will redirect back to /apache/oidc/callback after various checks.
  This request will contain authorization grant token and OIDC claims in
  parameters.

- mod_auth_openidc connects using back channel HTTP call to token endpoint
  (/freedombox/o/token/) with the authorization grant token and then obtains
  access token and refresh token. OIDC claims are checked using client_secret
  known only to FreedomBox IDP and mod_auth_openidc.

- The OIDC claims contains username as part of 'sub' claim. This is exported as
  REMOTE_USER header. 'freedombox_groups' contains the list of groups that
  FreedomBox account is part of. These, along with 'Require claim' Apache
  configuration directives, are used to determine if the user should get access
  to /foo path or not.

- The application providing /foo will have access to information such username
  and groups as part of REMOTE_USER and other OIDC_* environment variables.

- mod_auth_openidc also sets cookies that ensure that the whole process is not
  repeated when a second request for the path /foo is received.
"""

import ipaddress
import os

from django.utils.translation import gettext_lazy as _

from plinth import action_utils
from plinth import app as app_module
from plinth import cfg
from plinth.config import DropinConfigs
from plinth.daemon import Daemon, RelatedDaemon
from plinth.modules import names
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.oidc.components import OpenIDConnect
from plinth.package import Packages
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy, is_valid_user_name

from . import privileged


class ApacheApp(app_module.App):
    """FreedomBox app for Apache web server."""

    app_id = 'apache'

    _version = 15

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Apache HTTP Server'))
        self.add(info)

        packages = Packages('packages-apache', [
            'apache2', 'php-fpm', 'ssl-cert', 'uwsgi', 'uwsgi-plugin-python3',
            'libapache2-mod-auth-openidc'
        ])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-apache', [
            '/etc/apache2/conf-available/10-freedombox.conf',
            '/etc/apache2/conf-available/php-fpm-freedombox.conf',
            '/etc/fail2ban/jail.d/apache-auth-freedombox.conf',
        ])
        self.add(dropin_configs)

        web_server_ports = Firewall('firewall-web', _('Web Server'),
                                    ports=['http', 'https'], is_external=True)
        self.add(web_server_ports)

        freedombox_ports = Firewall(
            'firewall-plinth',
            format_lazy(_('{box_name} Web Interface (Plinth)'),
                        box_name=_(cfg.box_name)), ports=['http', 'https'],
            is_external=True)
        self.add(freedombox_ports)

        letsencrypt = LetsEncrypt('letsencrypt-apache', domains='*',
                                  daemons=['apache2'], reload_daemons=True)
        self.add(letsencrypt)

        openidconnect = OpenIDConnect(
            'openidconnect-apache', 'apache',
            _('Web app protected by FreedomBox'),
            redirect_uris=['https://{domain}/apache/oidc/callback'],
            skip_authorization=True)
        self.add(openidconnect)

        daemon = Daemon('daemon-apache', 'apache2')
        self.add(daemon)

        related_daemon = RelatedDaemon('related-daemon-apache', 'uwsgi')
        self.add(related_daemon)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(_on_domain_added)
        domain_removed.connect(_on_domain_removed)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup(old_version)
        self.enable()


def validate_host(hostname: str):
    """Check whether we are allowed to be called by a given name.

    This is to prevent DNS rebinding attacks and other poor consequences in the
    OpenID Connect protoctol.
    """
    if hostname in ('localhost', 'ip6-localhost', 'ip6-loopback'):
        return

    if hostname == action_utils.get_hostname():
        return

    if hostname in names.components.DomainName.list_names():
        return

    try:
        ipaddress.ip_address(hostname)
        return
    except ValueError:
        pass

    raise ValueError(f'Server not configured to be called as {hostname}')


def setup_oidc_client(netloc: str, hostname: str):
    """Setup OpenID Connect client configuration.

    netloc is hostname or IP address along with port as parsed by
    urllib.parse.urlparse() method from a URL.
    """
    validate_host(hostname)

    oidc = app_module.App.get('apache').get_component('openidconnect-apache')
    privileged.setup_oidc_client(netloc, oidc.client_id,
                                 oidc.get_client_secret())


def _on_domain_added(sender, domain_type, name='', description='',
                     services=None, **kwargs):
    """Add site specific configuration for a domain."""
    if name:
        privileged.domain_setup(name)


def _on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove site specific configuration for a domain."""
    if name:
        privileged.domain_remove(name)


# (U)ser (W)eb (S)ites


def uws_directory_of_user(user):
    """Return the directory of the given user's website."""
    return '/home/{}/public_html'.format(user)


def uws_url_of_user(user):
    """Return the url path of the given user's website."""
    return '/~{}/'.format(user)


def user_of_uws_directory(directory):
    """Return the user of a given user website directory."""
    if directory.startswith('/home/'):
        pos_ini = 6
    elif directory.startswith('home/'):
        pos_ini = 5
    else:
        return None

    pos_end = directory.find('/public_html')
    if pos_end == -1:
        return None

    user = directory[pos_ini:pos_end]
    return user if is_valid_user_name(user) else None


def user_of_uws_url(url):
    """Return the user of a given user website url path."""
    MISSING = -1

    pos_ini = url.find('~')
    if pos_ini == MISSING:
        return None

    pos_end = url.find('/', pos_ini)
    if pos_end == MISSING:
        pos_end = len(url)

    user = url[pos_ini + 1:pos_end]
    return user if is_valid_user_name(user) else None


def uws_directory_of_url(url):
    """Return the directory of the user's website for the given url path.

    Note: It doesn't return the full OS file path to the url path!
    """
    return uws_directory_of_user(user_of_uws_url(url))


def uws_url_of_directory(directory):
    """Return the url base path of the user's website for the given OS path.

    Note: It doesn't return the url path for the file!
    """
    return uws_url_of_user(user_of_uws_directory(directory))


def get_users_with_website():
    """Return a dictionary of users with actual website subdirectory."""

    def lst_sub_dirs(directory):
        """Return the list of subdirectories of the given directory."""
        return [
            name for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name))
        ]

    return {
        name: uws_url_of_user(name)
        for name in lst_sub_dirs('/home')
        if os.path.isdir(uws_directory_of_user(name))
    }
