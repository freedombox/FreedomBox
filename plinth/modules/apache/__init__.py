# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for Apache server."""

import os

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg
from plinth.config import DropinConfigs
from plinth.daemon import Daemon, RelatedDaemon
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.package import Packages
from plinth.utils import format_lazy, is_valid_user_name

from . import privileged


class ApacheApp(app_module.App):
    """FreedomBox app for Apache web server."""

    app_id = 'apache'

    _version = 12

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Apache HTTP Server'))
        self.add(info)

        packages = Packages('packages-apache', [
            'apache2', 'php-fpm', 'ssl-cert', 'uwsgi', 'uwsgi-plugin-python3'
        ])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-apache', [
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
                                  daemons=['apache2'])
        self.add(letsencrypt)

        daemon = Daemon('daemon-apache', 'apache2')
        self.add(daemon)

        related_daemon = RelatedDaemon('related-daemon-apache', 'uwsgi')
        self.add(related_daemon)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup(old_version)
        self.enable()


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
