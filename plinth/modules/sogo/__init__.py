# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure SOGo."""

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.daemon import Daemon, SharedDaemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.privileged import service as service_privileged
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('SOGo is a groupware server that provides a rich web interface for '
      'email, calendar, tasks, and contacts. Calendar, tasks, and contacts '
      'can also be accessed with various mobile and desktop applications '
      'using the CalDAV and CardDAV standards.'),
    format_lazy(
        _('Webmail works with the <a href="{email_url}">Postfix/Dovecot</a> '
          'email server app to retrieve, manage, and send email.'),
        email_url=reverse_lazy('email:index')),
    format_lazy(
        _('All users on {box_name} can login into and use SOGo. Mails '
          'delivered to their mailboxes by the email server app can be read '
          'and new mail can be sent out.'), box_name=_(cfg.box_name)),
]


class SOGoApp(app_module.App):
    """FreedomBox app for SOGo."""

    app_id = 'sogo'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               depends=['email'], name=_('SOGo'),
                               icon_filename='sogo', description=_description,
                               manual_page='SOGo', clients=manifest.clients,
                               tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-sogo', info.name, info.icon_filename,
                              info.tags, 'sogo:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-sogo', info.name,
                                      icon=info.icon_filename, url='/SOGo/',
                                      clients=info.clients, tags=info.tags)
        self.add(shortcut)

        # dpkg-dev is needed because plget command, part of
        # gnustep-base-runtime package, uses dpkg-architecture command but
        # there is no dependency on dpkg-dev.
        packages = Packages('packages-sogo',
                            ['sogo', 'postgresql', 'memcached', 'dpkg-dev'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-sogo', [
            '/etc/apache2/conf-available/sogo-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-sogo', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-sogo', 'sogo-freedombox',
                              urls=['https://{host}/SOGo/'])
        self.add(webserver)

        daemon1 = SharedDaemon('shared-daemon-sogo-memcached', 'memcached',
                               listen_ports=[(11211, 'tcp4')])
        self.add(daemon1)

        daemon2 = SharedDaemon('shared-daemon-sogo-postgresql', 'postgresql')
        self.add(daemon2)

        daemon3 = Daemon('daemon-sogo', 'sogo', listen_ports=[(20000, 'tcp4')])
        self.add(daemon3)

        backup_restore = SOGoBackupRestore('backup-restore-sogo',
                                           **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        service_privileged.try_restart('sogo')
        service_privileged.try_restart('memcached')

        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


class SOGoBackupRestore(BackupRestore):
    """Component to backup/restore SOGo."""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        privileged.dump_database()

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        privileged.restore_database()
