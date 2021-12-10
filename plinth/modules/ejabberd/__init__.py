# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure ejabberd server.
"""

import json
import logging

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules import config
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.coturn.components import TurnConfiguration, TurnConsumer
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.signals import (domain_added, post_hostname_change,
                            pre_hostname_change)
from plinth.utils import format_lazy

from . import manifest

_description = [
    _('XMPP is an open and standardized communication protocol. Here '
      'you can run and configure your XMPP server, called ejabberd.'),
    format_lazy(
        _('To actually communicate, you can use the <a href="{jsxc_url}">'
          'web client</a> or any other <a href=\'https://xmpp.org/'
          'software/clients\' target=\'_blank\'>XMPP client</a>. '
          'When enabled, ejabberd can be accessed by any '
          '<a href="{users_url}"> user with a {box_name} login</a>.'),
        box_name=_(cfg.box_name), users_url=reverse_lazy('users:index'),
        jsxc_url=reverse_lazy('jsxc:index')),
    format_lazy(
        _('ejabberd needs a STUN/TURN server for audio/video calls. '
          'Install the <a href={coturn_url}>Coturn</a> app or configure '
          'an external server.'), coturn_url=reverse_lazy('coturn:index'))
]

logger = logging.getLogger(__name__)

app = None


class EjabberdApp(app_module.App):
    """FreedomBox app for ejabberd."""

    app_id = 'ejabberd'

    _version = 4

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, depends=['coturn'],
            name=_('ejabberd'), icon_filename='ejabberd',
            short_description=_('Chat Server'), description=_description,
            manual_page='ejabberd', clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-ejabberd', info.name,
                              info.short_description, info.icon_filename,
                              'ejabberd:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-ejabberd', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('ejabberd:index'), clients=info.clients,
            login_required=True)
        self.add(shortcut)

        packages = Packages('packages-ejabberd', ['ejabberd'])
        self.add(packages)

        firewall = Firewall('firewall-ejabberd', info.name,
                            ports=['xmpp-client', 'xmpp-server',
                                   'xmpp-bosh'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-ejabberd', 'jwchat-plinth',
                              urls=['http://{host}/bosh/'])
        self.add(webserver)

        letsencrypt = LetsEncrypt(
            'letsencrypt-ejabberd', domains=get_domains, daemons=['ejabberd'],
            should_copy_certificates=True,
            private_key_path='/etc/ejabberd/letsencrypt/{domain}/ejabberd.pem',
            certificate_path='/etc/ejabberd/letsencrypt/{domain}/ejabberd.pem',
            user_owner='ejabberd', group_owner='ejabberd',
            managing_app='ejabberd')
        self.add(letsencrypt)

        daemon = Daemon(
            'daemon-ejabberd', 'ejabberd', listen_ports=[(5222, 'tcp4'),
                                                         (5222, 'tcp6'),
                                                         (5269, 'tcp4'),
                                                         (5269, 'tcp6'),
                                                         (5443, 'tcp4'),
                                                         (5443, 'tcp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-ejabberd',
                                          reserved_usernames=['ejabberd'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-ejabberd',
                                       **manifest.backup)
        self.add(backup_restore)

        turn = EjabberdTurnConsumer('turn-ejabberd')
        self.add(turn)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        pre_hostname_change.connect(on_pre_hostname_change)
        post_hostname_change.connect(on_post_hostname_change)
        domain_added.connect(on_domain_added)


class EjabberdTurnConsumer(TurnConsumer):
    """Component to manage Coturn configuration for ejabberd."""

    def on_config_change(self, config):
        """Add or update STUN/TURN configuration."""
        update_turn_configuration(config)


def setup(helper, old_version=None):
    """Install and configure the module."""
    domainname = config.get_domainname()
    logger.info('ejabberd service domainname - %s', domainname)

    helper.call('pre', actions.superuser_run, 'ejabberd',
                ['pre-install', '--domainname', domainname])
    # XXX: Configure all other domain names
    app.setup(old_version)
    helper.call('post',
                app.get_component('letsencrypt-ejabberd').setup_certificates,
                [domainname])
    helper.call('post', actions.superuser_run, 'ejabberd',
                ['setup', '--domainname', domainname])
    helper.call('post', app.enable)

    # Configure STUN/TURN only if there's a valid TLS domain set for Coturn
    configuration = app.get_component('turn-ejabberd').get_configuration()
    update_turn_configuration(configuration, force=True)


def get_domains():
    """Return the list of domains that ejabberd is interested in.

    XXX: Retrieve the list from ejabberd configuration.

    """
    if app.needs_setup():
        return []

    domain_name = config.get_domainname()
    if domain_name:
        return [domain_name]

    return []


def on_pre_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """
    Backup ejabberd database before hostname is changed.
    """
    del sender  # Unused
    del kwargs  # Unused
    if app.needs_setup():
        return

    actions.superuser_run('ejabberd', [
        'pre-change-hostname', '--old-hostname', old_hostname,
        '--new-hostname', new_hostname
    ])


def on_post_hostname_change(sender, old_hostname, new_hostname, **kwargs):
    """Update ejabberd config after hostname change."""
    del sender  # Unused
    del kwargs  # Unused
    if app.needs_setup():
        return

    actions.superuser_run('ejabberd', [
        'change-hostname', '--old-hostname', old_hostname, '--new-hostname',
        new_hostname
    ], run_in_background=True)


def on_domain_added(sender, domain_type, name, description='', services=None,
                    **kwargs):
    """Update ejabberd config after domain name change."""
    if app.needs_setup():
        return

    conf = actions.superuser_run('ejabberd', ['get-configuration'])
    conf = json.loads(conf)
    if name not in conf['domains']:
        actions.superuser_run('ejabberd', ['add-domain', '--domainname', name])
        app.get_component('letsencrypt-ejabberd').setup_certificates()


def update_turn_configuration(config: TurnConfiguration, managed=True,
                              force=False):
    """Update ejabberd's STUN/TURN server configuration."""
    if app.needs_setup():
        return

    params = ['configure-turn']
    params += ['--managed'] if managed else []
    actions.superuser_run('ejabberd', params, input=config.to_json().encode())


def get_turn_configuration() -> (TurnConfiguration, bool):
    """Get the latest STUN/TURN configuration."""
    json_config = actions.superuser_run('ejabberd', ['get-turn-config'])
    tc, managed = json.loads(json_config)
    return (TurnConfiguration(tc['domain'], tc['uris'],
                              tc['shared_secret']), managed)
