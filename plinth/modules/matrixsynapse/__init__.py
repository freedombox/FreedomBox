# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure matrix-synapse server.
"""

import logging
import os
import pathlib

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from ruamel.yaml.util import load_yaml_guess_indent

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.utils import Version

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 5

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
    _('To communicate, you can use the '
      '<a href="https://matrix.org/docs/projects/">available clients</a> '
      'for mobile, desktop and the web. <a href="https://riot.im/">Riot</a> '
      'client is recommended.')
]

port_forwarding_info = [('TCP', 8448)]

logger = logging.getLogger(__name__)

SERVER_NAME_PATH = "/etc/matrix-synapse/conf.d/server_name.yaml"
CONFIG_FILE_PATH = '/etc/matrix-synapse/homeserver.yaml'

app = None


class MatrixSynapseApp(app_module.App):
    """FreedomBox app for Matrix Synapse."""

    app_id = 'matrixsynapse'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Matrix Synapse'),
                               icon_filename='matrixsynapse',
                               short_description=_('Chat Server'),
                               description=_description,
                               manual_page='MatrixSynapse', clients=clients)
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


def init():
    """Initialize the matrix-synapse module."""
    global app
    app = MatrixSynapseApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'matrixsynapse',
                ['post-install'])
    helper.call('post', app.enable)
    app.get_component('letsencrypt-matrixsynapse').setup_certificates()


def force_upgrade(helper, packages):
    """Force upgrade matrix-synapse to resolve conffile prompt."""
    if 'matrix-synapse' not in packages:
        return False

    # Allow any lower version to upgrade to 1.15.*
    package = packages['matrix-synapse']
    if Version(package['new_version']) > Version('1.16~'):
        return False

    public_registration_status = get_public_registration_status()
    helper.install(['matrix-synapse'], force_configuration='new')
    actions.superuser_run('matrixsynapse', ['post-install'])
    if public_registration_status:
        actions.superuser_run('matrixsynapse',
                              ['public-registration', 'enable'])

    return True


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


def get_public_registration_status():
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
