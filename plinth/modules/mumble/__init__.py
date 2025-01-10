# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Mumble server.
"""

import pathlib

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.translation import gettext_noop

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.diagnostic_check import DiagnosticCheck, Result
from plinth.modules import names
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.letsencrypt.components import LetsEncrypt
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages, install
from plinth.utils import Version

from . import manifest, privileged

_description = [
    _('Mumble is an open source, low-latency, encrypted, high quality '
      'voice chat software.'),
    _('You can connect to your Mumble server on the regular Mumble port '
      '64738. <a href="http://mumble.info">Clients</a> to connect to Mumble '
      'from your desktop and mobile devices are available.')
]


class MumbleApp(app_module.App):
    """FreedomBox app for Mumble."""

    app_id = 'mumble'

    _version = 2

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Mumble'),
            icon_filename='mumble', description=_description,
            manual_page='Mumble', clients=manifest.clients, tags=manifest.tags,
            donation_url='https://wiki.mumble.info/wiki/Donate')
        self.add(info)

        menu_item = menu.Menu('menu-mumble', info.name, info.short_description,
                              'mumble', 'mumble:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-mumble', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('mumble:index'), clients=info.clients)
        self.add(shortcut)

        packages = Packages('packages-mumble', ['mumble-server'])
        self.add(packages)

        firewall = Firewall('firewall-mumble', info.name,
                            ports=['mumble-plinth'], is_external=True)
        self.add(firewall)

        letsencrypt = LetsEncrypt(
            'letsencrypt-mumble', domains=get_domains,
            daemons=['mumble-server'], should_copy_certificates=True,
            private_key_path='/var/lib/mumble-server/privkey.pem',
            certificate_path='/var/lib/mumble-server/fullchain.pem',
            user_owner='mumble-server', group_owner='mumble-server',
            managing_app='mumble')
        self.add(letsencrypt)

        daemon = Daemon(
            'daemon-mumble', 'mumble-server', listen_ports=[(64738, 'tcp4'),
                                                            (64738, 'tcp6'),
                                                            (64738, 'udp4'),
                                                            (64738, 'udp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-mumble',
                                          reserved_usernames=['mumble-server'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-mumble',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()

        self.get_component('letsencrypt-mumble').setup_certificates()

    def force_upgrade(self, packages):
        """Force upgrade mumble-server to resolve conffile prompts."""
        if 'mumble-server' not in packages:
            return False

        # Allow upgrades within 1.3.*
        package = packages['mumble-server']
        if Version(package['new_version']) > Version('1.4~'):
            return False

        install(['mumble-server'], force_configuration='new')
        privileged.setup()
        return True

    def diagnose(self) -> list[DiagnosticCheck]:
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(_diagnose_config())
        return results


def get_available_domains():
    """Return an iterator with all domains able to have a certificate."""
    return (domain.name for domain in names.components.DomainName.list()
            if domain.domain_type.can_have_certificate)


def get_domain():
    """Read TLS domain from config file select first available if none."""
    domain = privileged.get_domain()
    if not domain:
        domain = next(get_available_domains(), None)
        privileged.set_domain(domain)

    return domain


def get_domains():
    """Return a list with the configured domains."""
    if not pathlib.Path('/var/lib/mumble-server/').exists():
        return []

    domain = get_domain()
    if domain:
        return [domain]

    return []


def _diagnose_config() -> DiagnosticCheck:
    """Check that configuration changes made during setup are in place."""
    result = Result.PASSED if privileged.check_setup() else Result.FAILED
    return DiagnosticCheck('mumble-config',
                           gettext_noop('Mumble server is configured'), result)
