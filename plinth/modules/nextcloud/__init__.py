# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Nextcloud."""

import contextlib

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon, SharedDaemon
from plinth.modules.apache.components import (Webserver, diagnose_url,
                                              diagnose_url_on_all)
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.modules.names.components import DomainName
from plinth.package import Packages
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('Nextcloud is a self-hosted productivity platform which provides '
      'private and secure functions for file sharing, collaborative work, '
      'and more. Nextcloud includes the Nextcloud server, client applications '
      'for desktop computers, and mobile clients. The Nextcloud server '
      'provides a well integrated web interface.'),
    _('All users of FreedomBox can use Nextcloud. To perform administrative '
      f'actions, use the <strong>"{privileged.GUI_ADMIN}"</strong> user after '
      'setting a password here.'),
    format_lazy(
        _('Please note that Nextcloud is installed and run inside a container '
          'provided by the Nextcloud project. Security, quality, privacy and '
          'legal reviews are done by the upstream project and not by '
          'Debian/{box_name}. Updates are performed following an independent '
          'cycle.'), box_name=_(cfg.box_name)),
    format_lazy('<div class="alert alert-warning" role="alert">{}</div>',
                _('This app is experimental.')),
]


class NextcloudApp(app_module.App):
    """FreedomBox app for Nextcloud."""

    app_id = 'nextcloud'

    _version = 1

    configure_when_disabled = False

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Nextcloud'),
            icon_filename='nextcloud',
            short_description=_('File Storage & Collaboration'),
            description=_description, manual_page='Nextcloud',
            clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-nextcloud', info.name,
                              info.short_description, info.icon_filename,
                              'nextcloud:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-nextcloud', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/nextcloud/', clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        packages = Packages('packages-nextcloud', [
            'podman', 'default-mysql-server', 'python3-iso3166',
            'redis-server', 'php-redis'
        ], conflicts=['libpam-tmpdir'],
                            conflicts_action=Packages.ConflictsAction.REMOVE)
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-nextcloud', [
            '/etc/apache2/conf-available/nextcloud-freedombox.conf',
            '/etc/redis/conf.d/freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-nextcloud', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-nextcloud', ['9000'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-nextcloud', 'nextcloud-freedombox')
        self.add(webserver)

        daemon = SharedDaemon('shared-daemon-podman-auto-update',
                              'podman-auto-update.timer')
        self.add(daemon)

        daemon = SharedDaemon('shared-daemon-nextcloud-redis', 'redis-server',
                              listen_ports=[(6379, 'tcp4')])
        self.add(daemon)

        daemon = SharedDaemon('shared-daemon-nextcloud-mysql', 'mysql')
        self.add(daemon)

        daemon = NextcloudDaemon('daemon-nextcloud', 'nextcloud-freedombox')
        self.add(daemon)

        daemon = Daemon('daemon-nextcloud-timer',
                        'nextcloud-cron-freedombox.timer')
        self.add(daemon)

        backup_restore = NextcloudBackupRestore('backup-restore-nextcloud',
                                                **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(_on_domain_added)
        domain_removed.connect(_on_domain_removed)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        # Drop-in configs need to be enabled for setup to succeed
        self.get_component('dropin-configs-nextcloud').enable()
        redis = self.get_component('shared-daemon-nextcloud-redis')
        mysql = self.get_component('shared-daemon-nextcloud-mysql')
        nextcloud = self.get_component('daemon-nextcloud')

        # Determine whether app should be disabled after setup
        should_disable = old_version and not nextcloud.is_enabled()

        with redis.ensure_running():
            with mysql.ensure_running():
                # Database needs to be running for successful initialization or
                # upgrade of Nextcloud database.
                privileged.setup()
                _set_trusted_domains()

        if should_disable:
            self.disable()

        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        privileged.uninstall()
        super().uninstall()

    def diagnose(self):
        """Run diagnostics and return the results.

        When an override domain is set, that domain and all other addresses are
        expected to work. This is because Nextcloud will accept any Host: HTTP
        header and then override it with the provided domain name. When
        override domain is not set, only the configured trusted domains along
        with local IP addresses are allowed. Others are rejected with an error.
        """
        results = super().diagnose()

        kwargs = {'check_certificate': False}
        url = 'https://{domain}/nextcloud/login'
        domain = privileged.get_override_domain()
        if domain:
            results.append(diagnose_url(url.format(domain=domain), **kwargs))
            results += diagnose_url_on_all(url.format(domain='{host}'),
                                           **kwargs)
        else:
            local_addresses = [('localhost', '4'), ('localhost', '6'),
                               ('127.0.0.1', '4'), ('[::1]', '6')]
            for address, kind in local_addresses:
                results.append(
                    diagnose_url(url.format(domain=address), kind=kind,
                                 **kwargs))

        results.append(diagnose_url('docker.com'))

        return results


class NextcloudDaemon(Daemon):
    """Component to manage Nextcloud container service."""

    def is_enabled(self):
        """Return if the daemon/unit is enabled."""
        return privileged.is_enabled()

    def enable(self):
        """Run operations to enable the daemon/unit."""
        super().enable()
        privileged.enable()

    def disable(self):
        """Run operations to disable the daemon/unit."""
        super().disable()
        privileged.disable()


class NextcloudBackupRestore(BackupRestore):
    """Component to backup/restore Nextcloud."""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        with _ensure_nextcloud_running():
            privileged.dump_database()

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        with _ensure_nextcloud_running():
            privileged.restore_database()


def _on_domain_added(sender, domain_type, name='', description='',
                     services=None, **kwargs):
    """Add domain to list of trusted domains."""
    app = app_module.App.get('nextcloud')
    if app.needs_setup():
        return

    _set_trusted_domains()


def _on_domain_removed(sender, domain_type, name='', **kwargs):
    """Update the list of trusted domains."""
    app = app_module.App.get('nextcloud')
    if app.needs_setup():
        return

    _set_trusted_domains()


def _set_trusted_domains():
    """Set the list of trusted domains."""
    all_domains = DomainName.list_names()
    with _ensure_nextcloud_running():
        privileged.set_trusted_domains(list(all_domains))


@contextlib.contextmanager
def _ensure_nextcloud_running():
    """Ensure the nextcloud is running and returns to original state."""
    app = app_module.App.get('nextcloud')
    app.get_component('dropin-configs-nextcloud').enable()
    mysql = app.get_component('shared-daemon-nextcloud-mysql')
    redis = app.get_component('shared-daemon-nextcloud-redis')
    container = app.get_component('daemon-nextcloud')
    with mysql.ensure_running():
        with redis.ensure_running():
            with container.ensure_running():
                yield
