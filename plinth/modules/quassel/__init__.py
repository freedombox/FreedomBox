# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for Quassel.
"""

import pathlib

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules import names
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.users.components import UsersAndGroups
from plinth.utils import format_lazy

from . import manifest

version = 1

managed_services = ['quasselcore']

managed_packages = ['quassel-core']

managed_paths = [pathlib.Path('/var/lib/quassel/')]

_description = [
    format_lazy(
        _('Quassel is an IRC application that is split into two parts, a '
          '"core" and a "client". This allows the core to remain connected '
          'to IRC servers, and to continue receiving messages, even when '
          'the client is disconnected. {box_name} can run the Quassel '
          'core service keeping you always online and one or more Quassel '
          'clients from a desktop or a mobile can be used to connect and '
          'disconnect from it.'), box_name=_(cfg.box_name)),
    _('You can connect to your Quassel core on the default Quassel port '
      '4242.  Clients to connect to Quassel from your '
      '<a href="http://quassel-irc.org/downloads">desktop</a> and '
      '<a href="http://quasseldroid.iskrembilen.com/">mobile</a> devices '
      'are available.'),
]

app = None


class QuasselApp(app_module.App):
    """FreedomBox app for Quassel."""

    app_id = 'quassel'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Quassel'), icon_filename='quassel',
                               short_description=_('IRC Client'),
                               description=_description, manual_page='Quassel',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-quassel', info.name,
                              info.short_description, info.icon_filename,
                              'quassel:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-quassel', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('quassel:index'), clients=info.clients,
            login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-quassel', info.name,
                            ports=['quassel-plinth'], is_external=True)
        self.add(firewall)

        letsencrypt = LetsEncrypt(
            'letsencrypt-quassel', domains=get_domains,
            daemons=managed_services, should_copy_certificates=True,
            private_key_path='/var/lib/quassel/quasselCert.pem',
            certificate_path='/var/lib/quassel/quasselCert.pem',
            user_owner='quasselcore', group_owner='quassel',
            managing_app='quassel')
        self.add(letsencrypt)

        daemon = Daemon('daemon-quassel', managed_services[0],
                        listen_ports=[(4242, 'tcp4'), (4242, 'tcp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-quasselcore',
                                          reserved_usernames=['quasselcore'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-quassel',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
    app.get_component('letsencrypt-quassel').setup_certificates()


def get_available_domains():
    """Return an iterator with all domains able to have a certificate."""
    return (domain.name for domain in names.components.DomainName.list()
            if domain.domain_type.can_have_certificate)


def set_domain(domain):
    """Set the TLS domain by writing a file to data directory."""
    if domain:
        actions.superuser_run('quassel', ['set-domain', domain])


def get_domain():
    """Read TLS domain from config file select first available if none."""
    domain = None
    try:
        with open('/var/lib/quassel/domain-freedombox') as file_handle:
            domain = file_handle.read().strip()
    except FileNotFoundError:
        pass

    if not domain:
        domain = next(get_available_domains(), None)
        set_domain(domain)

    return domain


def get_domains():
    """Return a list with the configured domain for quassel."""
    # If not installed, return empty. But work while installing too.
    if not pathlib.Path('/var/lib/quassel/').exists():
        return []

    domain = get_domain()
    if domain:
        return [domain]

    return []
