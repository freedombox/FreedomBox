# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Nextcloud."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon, SharedDaemon
from plinth.modules.apache.components import Webserver, diagnose_url
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('Nextcloud is a self-hosted productivity platform which provides '
      'private and secure functions for file sharing, collaborative work, '
      'and more. Nextcloud includes the Nextcloud server, client applications '
      'for desktop computers, and mobile clients. The Nextcloud server '
      'provides a well integrated web interface.'),
    _('All users of FreedomBox can use Nextcloud.'),
    _('To perform administrative actions, use the '
      f'<strong>"{privileged.GUI_ADMIN}"</strong> user.'),
    _('You can set a new password in the "Configuration" section below.'),
    _('Please note, that Nextcloud isn\'t maintained by Debian, which means '
      'security and feature updates are applied independently.')
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

        packages = Packages('packages-nextcloud',
                            ['podman', 'default-mysql-server'],
                            conflicts=['libpam-tmpdir'],
                            conflicts_action=Packages.ConflictsAction.REMOVE)
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-nextcloud', [
            '/etc/apache2/conf-available/nextcloud-freedombox.conf',
            '/etc/fail2ban/jail.d/nextcloud-freedombox.conf',
            '/etc/fail2ban/filter.d/nextcloud-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-nextcloud', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-nextcloud', ['8181'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-nextcloud', 'nextcloud-freedombox',
                              urls=['https://{host}/nextcloud/login'])
        self.add(webserver)

        daemon = Daemon('daemon-nextcloud', 'nextcloud-fbx')
        self.add(daemon)

        daemon = Daemon('daemon-nextcloud-timer', 'nextcloud-cron-fbx.timer')
        self.add(daemon)

        daemon = SharedDaemon('shared-daemon-podman-auto-update',
                              'podman-auto-update.timer')
        self.add(daemon)

        daemon = SharedDaemon('shared-daemon-nextcloud-redis', 'redis-server',
                              listen_ports=[(6379, 'tcp4')])
        self.add(daemon)

        daemon = SharedDaemon('shared-daemon-nextcloud-mysql', 'mysql')
        self.add(daemon)

        backup_restore = NextcloudBackupRestore('backup-restore-nextcloud',
                                                **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        privileged.uninstall()
        super().uninstall()

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()
        results.append(diagnose_url('docker.com'))
        return results


class NextcloudBackupRestore(BackupRestore):
    """Component to backup/restore Nextcloud."""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        privileged.dump_database()

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        privileged.restore_database()
