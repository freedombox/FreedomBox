# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for Quassel."""

import pathlib

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules import names
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

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


class QuasselApp(app_module.App):
    """FreedomBox app for Quassel."""

    app_id = 'quassel'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Quassel'), icon_filename='quassel',
                               short_description=_('IRC Client'),
                               description=_description, manual_page='Quassel',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-quassel', info.name,
                              info.short_description, info.icon_filename,
                              'quassel:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-quassel', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('quassel:index'), clients=info.clients,
            login_required=True)
        self.add(shortcut)

        packages = Packages('packages-quassel', ['quassel-core'])
        self.add(packages)

        firewall = Firewall('firewall-quassel', info.name,
                            ports=['quassel-plinth'], is_external=True)
        self.add(firewall)

        letsencrypt = LetsEncrypt(
            'letsencrypt-quassel', domains=get_domains,
            daemons=['quasselcore'], should_copy_certificates=True,
            private_key_path='/var/lib/quassel/quasselCert.pem',
            certificate_path='/var/lib/quassel/quasselCert.pem',
            user_owner='quasselcore', group_owner='quassel',
            managing_app='quassel')
        self.add(letsencrypt)

        daemon = Daemon('daemon-quassel', 'quasselcore',
                        listen_ports=[(4242, 'tcp4'), (4242, 'tcp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-quasselcore',
                                          reserved_usernames=['quasselcore'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-quassel',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()

        self.get_component('letsencrypt-quassel').setup_certificates()


def set_domain(domain):
    """Set the TLS domain by writing a file to data directory."""
    if domain:
        privileged.set_domain(domain)


def get_domain():
    """Read TLS domain from config file select first available if none."""
    domain = None
    try:
        with open('/var/lib/quassel/domain-freedombox',
                  encoding='utf-8') as file_handle:
            domain = file_handle.read().strip()
    except FileNotFoundError:
        pass

    if not domain:
        domain = next(names.get_available_tls_domains(), None)
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
