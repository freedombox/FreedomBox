# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure matrix-synapse server.
"""

import logging
import os
import pathlib
from typing import List

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from ruamel.yaml.util import load_yaml_guess_indent

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.coturn.components import TurnConfiguration, TurnConsumer
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.package import Packages
from plinth.utils import format_lazy, is_non_empty_file

from . import manifest

version = 7

managed_services = ['matrix-synapse']

managed_packages = ['matrix-synapse', 'matrix-synapse-ldap3']

managed_paths = [pathlib.Path('/etc/matrix-synapse/')]

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

depends = ['coturn']

logger = logging.getLogger(__name__)

CONF_DIR = "/etc/matrix-synapse/conf.d/"

ORIG_CONF_PATH = '/etc/matrix-synapse/homeserver.yaml'
SERVER_NAME_PATH = CONF_DIR + 'server_name.yaml'
STATIC_CONF_PATH = CONF_DIR + 'freedombox-static.yaml'
LISTENERS_CONF_PATH = CONF_DIR + 'freedombox-listeners.yaml'
REGISTRATION_CONF_PATH = CONF_DIR + 'freedombox-registration.yaml'
TURN_CONF_PATH = CONF_DIR + 'freedombox-turn.yaml'
OVERRIDDEN_TURN_CONF_PATH = CONF_DIR + 'turn.yaml'

app = None


class MatrixSynapseApp(app_module.App):
    """FreedomBox app for Matrix Synapse."""

    app_id = 'matrixsynapse'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=version, name=_('Matrix Synapse'),
            icon_filename='matrixsynapse', short_description=_('Chat Server'),
            description=_description, manual_page='MatrixSynapse',
            clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-matrixsynapse', info.name,
                              info.short_description, 'matrixsynapse',
                              'matrixsynapse:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-matrixsynapse', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('matrixsynapse:index'),
            clients=info.clients, login_required=True)
        self.add(shortcut)

        packages = Packages('packages-matrixsynapse', managed_packages)
        self.add(packages)

        firewall = Firewall('firewall-matrixsynapse', info.name,
                            ports=['matrix-synapse-plinth'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-matrixsynapse',
                              'matrix-synapse-plinth',
                              urls=['https://{host}/_matrix/client/versions'])
        self.add(webserver)

        letsencrypt = LetsEncrypt(
            'letsencrypt-matrixsynapse', domains=get_domains,
            daemons=[managed_services[0]], should_copy_certificates=True,
            private_key_path='/etc/matrix-synapse/homeserver.tls.key',
            certificate_path='/etc/matrix-synapse/homeserver.tls.crt',
            user_owner='matrix-synapse', group_owner='nogroup',
            managing_app='matrixsynapse')
        self.add(letsencrypt)

        daemon = Daemon('daemon-matrixsynapse', managed_services[0],
                        listen_ports=[(8008, 'tcp4'), (8448, 'tcp4')])
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-matrixsynapse',
                                       **manifest.backup)
        self.add(backup_restore)

        turn = MatrixSynapseTurnConsumer('turn-matrixsynapse')
        self.add(turn)


class MatrixSynapseTurnConsumer(TurnConsumer):
    """Component to manage Coturn configuration for Matrix Synapse."""

    def on_config_change(self, config: TurnConfiguration):
        """Add or update STUN/TURN configuration."""
        update_turn_configuration(config)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    if old_version and old_version < 6:
        helper.call('post', upgrade, helper)
    else:
        helper.call('post', actions.superuser_run, 'matrixsynapse',
                    ['post-install'])

    if not old_version:
        helper.call('post', app.enable)

    app.get_component('letsencrypt-matrixsynapse').setup_certificates()

    # Configure STUN/TURN only if there's a valid TLS domain set for Coturn
    config = app.get_component('turn-matrixsynapse').get_configuration()
    update_turn_configuration(config, force=True)


def upgrade(helper):
    """Upgrade matrix-synapse configuration to avoid conffile prompt."""
    public_registration_status = get_public_registration_status()
    actions.superuser_run('matrixsynapse', ['move-old-conf'])
    helper.install(['matrix-synapse'], force_configuration='new',
                   reinstall=True, force_missing_configuration=True)
    actions.superuser_run('matrixsynapse', ['post-install'])
    if public_registration_status:
        actions.superuser_run('matrixsynapse',
                              ['public-registration', 'enable'])


def setup_domain(domain_name):
    """Configure a domain name for matrixsynapse."""
    app.get_component('letsencrypt-matrixsynapse').setup_certificates(
        [domain_name])
    actions.superuser_run('matrixsynapse',
                          ['setup', '--domain-name', domain_name])


def is_setup():
    """Return whether the Matrix Synapse server is setup."""
    return os.path.exists(SERVER_NAME_PATH)


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

    with open(SERVER_NAME_PATH) as config_file:
        config, _, _ = load_yaml_guess_indent(config_file)

    return config['server_name']


def get_turn_configuration() -> (List[str], str, bool):
    """Return TurnConfiguration if setup else empty."""
    for file_path, managed in ((OVERRIDDEN_TURN_CONF_PATH, False),
                               (TURN_CONF_PATH, True)):
        if is_non_empty_file(file_path):
            with open(file_path) as config_file:
                config, _, _ = load_yaml_guess_indent(config_file)
                return (TurnConfiguration(None, config['turn_uris'],
                                          config['turn_shared_secret']),
                        managed)

    return (TurnConfiguration(), True)


def get_public_registration_status() -> bool:
    """Return whether public registration is enabled."""
    output = actions.superuser_run('matrixsynapse',
                                   ['public-registration', 'status'])
    return output.strip() == 'enabled'


def get_certificate_status():
    """Return the status of certificate for the configured domain."""
    status = app.get_component('letsencrypt-matrixsynapse').get_status()
    if not status:
        return 'no-domains'

    return list(status.values())[0]


def update_turn_configuration(config: TurnConfiguration, managed=True,
                              force=False):
    """Update the STUN/TURN server configuration."""
    setup_helper = globals()['setup_helper']
    if not force and setup_helper.get_state() == 'needs-setup':
        return

    params = ['configure-turn']
    params += ['--managed'] if managed else []
    actions.superuser_run('matrixsynapse', params,
                          input=config.to_json().encode())
