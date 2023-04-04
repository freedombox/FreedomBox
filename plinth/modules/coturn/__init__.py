# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Coturn server."""

import logging
import pathlib

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import menu
from plinth.daemon import Daemon
from plinth.modules import names
from plinth.modules.backups.components import BackupRestore
from plinth.modules.coturn.components import TurnConfiguration, TurnConsumer
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('Coturn is a server to facilitate audio/video calls and conferences by '
      'providing an implementation of TURN and STUN protocols. WebRTC, SIP '
      'and other communication servers can use it to establish a call between '
      'parties who are otherwise unable connect to each other.'),
    format_lazy(
        _('It is not meant to be used directly by users. Servers such as '
          '<a href="{ms_url}">Matrix Synapse</a> or <a href="{e_url}">ejabberd'
          '</a> need to be configured with the details provided here.'),
        ms_url=reverse_lazy('matrixsynapse:index'),
        e_url=reverse_lazy('ejabberd:index')),
]

logger = logging.getLogger(__name__)


class CoturnApp(app_module.App):
    """FreedomBox app for Coturn."""

    app_id = 'coturn'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Coturn'), icon_filename='coturn',
                               short_description=_('VoIP Helper'),
                               description=_description, manual_page='Coturn')
        self.add(info)

        menu_item = menu.Menu('menu-coturn', info.name, info.short_description,
                              info.icon_filename, 'coturn:index',
                              parent_url_name='apps')
        self.add(menu_item)

        # Include sqlite3 to prevent removal of coturn from removal of
        # roundcube.
        packages = Packages('packages-coturn', ['coturn', 'sqlite3'])
        self.add(packages)

        firewall = Firewall('firewall-coturn', info.name,
                            ports=['coturn-freedombox'], is_external=True)
        self.add(firewall)

        letsencrypt = LetsEncrypt(
            'letsencrypt-coturn', domains=get_domains, daemons=['coturn'],
            should_copy_certificates=True,
            private_key_path='/etc/coturn/certs/pkey.pem',
            certificate_path='/etc/coturn/certs/cert.pem',
            user_owner='turnserver', group_owner='turnserver',
            managing_app='coturn')
        self.add(letsencrypt)

        daemon = Daemon(
            'daemon-coturn', 'coturn', listen_ports=[(3478, 'udp4'),
                                                     (3478, 'udp6'),
                                                     (3478, 'tcp4'),
                                                     (3478, 'tcp6'),
                                                     (3479, 'udp4'),
                                                     (3479, 'udp6'),
                                                     (3479, 'tcp4'),
                                                     (3479, 'tcp6'),
                                                     (5349, 'udp4'),
                                                     (5349, 'udp6'),
                                                     (5349, 'tcp4'),
                                                     (5349, 'tcp6'),
                                                     (5350, 'udp4'),
                                                     (5350, 'udp6'),
                                                     (5350, 'tcp4'),
                                                     (5350, 'tcp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-coturn',
                                          reserved_usernames=['turnserver'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-coturn',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if old_version == 0:
            self.enable()

        self.get_component('letsencrypt-coturn').setup_certificates()
        notify_configuration_change()


def get_available_domains():
    """Return an iterator with all domains able to have a certificate."""
    return (domain.name for domain in names.components.DomainName.list()
            if domain.domain_type.can_have_certificate)


def get_domain():
    """Read TLS domain from config file select first available if none."""
    config = get_config()
    if config.domain:
        return config.domain

    domain = next(get_available_domains(), None)
    set_domain(domain)

    return domain


def get_domains():
    """Return a list with the configured domains."""
    # If not installed, return empty. But work while installing too.
    if not pathlib.Path('/etc/coturn/freedombox.conf').exists():
        return []

    domain = get_domain()
    if domain:
        return [domain]

    return []


def set_domain(domain):
    """Set the TLS domain by writing a file to data directory."""
    if domain:
        privileged.set_domain(domain)
        notify_configuration_change()


def get_config():
    """Return the coturn server configuration."""
    config = privileged.get_config()
    return TurnConfiguration(config['realm'], [], config['static_auth_secret'])


def notify_configuration_change():
    """Notify all coturn components about the new configuration."""
    logger.info('Notifying STUN/TURN consumers about configuration change')
    config = get_config()
    for component in TurnConsumer.list():
        component.on_config_change(config)
