# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure matrix-synapse server."""

import logging
import os

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from ruamel.yaml.util import load_yaml_guess_indent

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.coturn.components import TurnConfiguration, TurnConsumer
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.package import Packages, install
from plinth.utils import format_lazy, is_non_empty_file

from . import manifest, privileged

_description = [
    _('<a href="https://matrix.org/docs/guides/faq.html">Matrix</a> is an new '
      'ecosystem for open, federated instant messaging and VoIP. Synapse is a '
      'server implementing the Matrix protocol. It provides chat groups, '
      'audio/video calls, end-to-end encryption, multiple device '
      'synchronization and does not require phone numbers to work. Users on a '
      'given Matrix server can converse with users on all other Matrix '
      'servers via federation.'),
    format_lazy(
        _('Matrix Synapse needs a STUN/TURN server for audio/video calls. '
          'Install the <a href={coturn_url}>Coturn</a> app or configure '
          'an external server.'), coturn_url=reverse_lazy('coturn:index'))
]

logger = logging.getLogger(__name__)


class MatrixSynapseApp(app_module.App):
    """FreedomBox app for Matrix Synapse."""

    app_id = 'matrixsynapse'

    _version = 10

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               depends=['coturn'], name=_('Matrix Synapse'),
                               icon_filename='matrixsynapse',
                               description=_description,
                               manual_page='MatrixSynapse',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-matrixsynapse', info.name,
                              info.icon_filename, info.tags,
                              'matrixsynapse:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-matrixsynapse', info.name, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('matrixsynapse:index'),
            clients=info.clients, tags=info.tags, login_required=True)
        self.add(shortcut)

        # Include python3-psycopg2 to prevent accidental uninstall
        # (see issue #2298).
        packages = Packages(
            'packages-matrixsynapse',
            ['matrix-synapse', 'matrix-synapse-ldap3', 'python3-psycopg2'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-matrixsynapse', [
            '/etc/apache2/conf-available/matrix-synapse-plinth.conf',
            '/etc/fail2ban/jail.d/matrix-auth-freedombox.conf',
            '/etc/fail2ban/filter.d/matrix-auth-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-matrixsynapse', info.name,
                            ports=['matrix-synapse-plinth'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-matrixsynapse',
                              'matrix-synapse-plinth',
                              urls=['https://{host}/_matrix/client/versions'])
        self.add(webserver)

        letsencrypt = LetsEncrypt(
            'letsencrypt-matrixsynapse', domains=get_domains,
            daemons=['matrix-synapse'], should_copy_certificates=True,
            private_key_path='/etc/matrix-synapse/homeserver.tls.key',
            certificate_path='/etc/matrix-synapse/homeserver.tls.crt',
            user_owner='matrix-synapse', group_owner='nogroup',
            managing_app='matrixsynapse')
        self.add(letsencrypt)

        daemon = Daemon('daemon-matrixsynapse', 'matrix-synapse',
                        listen_ports=[(8008, 'tcp4'), (8448, 'tcp4')])
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-matrixsynapse',
                                       **manifest.backup)
        self.add(backup_restore)

        turn = MatrixSynapseTurnConsumer('turn-matrixsynapse')
        self.add(turn)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if old_version and old_version < 6:
            upgrade()
        else:
            privileged.post_install()

        if old_version and old_version <= 7:
            privileged.fix_public_registrations()

        if not old_version:
            self.enable()

        self.get_component('letsencrypt-matrixsynapse').setup_certificates()

        if not old_version or get_turn_configuration()[1]:
            # Configure STUN/TURN only if there's a valid TLS domain set for
            # Coturn. Do this if app is being freshly installed or if it is
            # previously installed and configured to use STUN/TURN
            # auto-management.
            config = self.get_component(
                'turn-matrixsynapse').get_configuration()
            update_turn_configuration(config, force=True)

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


class MatrixSynapseTurnConsumer(TurnConsumer):
    """Component to manage Coturn configuration for Matrix Synapse."""

    def on_config_change(self, config: TurnConfiguration):
        """Add or update STUN/TURN configuration."""
        update_turn_configuration(config)


def upgrade():
    """Upgrade matrix-synapse configuration to avoid conffile prompt."""
    config = privileged.get_config()
    privileged.move_old_conf()
    install(['matrix-synapse'], force_configuration='new', reinstall=True,
            force_missing_configuration=True)
    privileged.post_install()
    privileged.set_config(**config)


def setup_domain(domain_name):
    """Configure a domain name for matrixsynapse."""
    app = app_module.App.get('matrixsynapse')
    app.get_component('letsencrypt-matrixsynapse').setup_certificates(
        [domain_name])
    privileged.setup(domain_name)


def is_setup():
    """Return whether the Matrix Synapse server is setup."""
    return os.path.exists(privileged.SERVER_NAME_PATH)


def get_domains():
    """Return a list of domains this app is interested in."""
    domain = get_configured_domain_name()
    if domain:
        return [domain]

    return []


def get_configured_domain_name():
    """Return the currently configured domain name."""
    if not is_setup():
        return None

    with open(privileged.SERVER_NAME_PATH, encoding='utf-8') as config_file:
        config, _, _ = load_yaml_guess_indent(config_file)

    return config['server_name']


def get_turn_configuration() -> tuple[TurnConfiguration, bool]:
    """Return TurnConfiguration if setup else empty."""
    for file_path, managed in ((privileged.OVERRIDDEN_TURN_CONF_PATH, False),
                               (privileged.TURN_CONF_PATH, True)):
        if is_non_empty_file(file_path):
            with open(file_path, encoding='utf-8') as config_file:
                config, _, _ = load_yaml_guess_indent(config_file)
                return (TurnConfiguration(None, config['turn_uris'],
                                          config['turn_shared_secret']),
                        managed)

    return (TurnConfiguration(), True)


def get_certificate_status():
    """Return the status of certificate for the configured domain."""
    app = app_module.App.get('matrixsynapse')
    status = app.get_component('letsencrypt-matrixsynapse').get_status()
    if not status:
        return 'no-domains'

    return list(status.values())[0]


def update_turn_configuration(config: TurnConfiguration, managed=True,
                              force=False):
    """Update the STUN/TURN server configuration."""
    app = app_module.App.get('matrixsynapse')
    if not force and app.needs_setup():
        return

    privileged.configure_turn(managed, config.to_json())
