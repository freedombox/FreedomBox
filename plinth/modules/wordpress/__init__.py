# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure WordPress.
"""

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest

PUBLIC_ACCESS_FILE = '/etc/wordpress/is_public'

_description = [
    _('WordPress is a popular way to create and manage websites and blogs. '
      'Content can be managed using a visual interface. Layout and '
      'functionality of the web pages can be customized. Appearance can be '
      'chosen using themes. Administration interface and produced web pages '
      'are suitable for mobile devices.'),
    format_lazy(
        _('You need to run WordPress setup by visiting the app before making '
          'the site publicly available below. Setup must be run when '
          'accessing {box_name} with the correct domain name. Enable '
          'permalinks in administrator interface for better URLs to your '
          'pages and posts.'), box_name=_(cfg.box_name)),
    _('WordPress has its own user accounts. First administrator account is '
      'created during setup. Bookmark the <a '
      'href="/wordpress/wp-admin/">admin page</a> to reach administration '
      'interface in the future.'),
    _('After a major version upgrade, you need to manually run database '
      'upgrade from administrator interface. Additional plugins or themes may '
      'be installed and upgraded at your own risk.'),
]

app = None


class WordPressApp(app_module.App):
    """FreedomBox app for WordPress."""

    app_id = 'wordpress'

    _version = 2

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('WordPress'),
            icon_filename='wordpress', short_description=_('Website and Blog'),
            description=_description, manual_page='WordPress',
            clients=manifest.clients,
            donation_url='https://wordpressfoundation.org/donate/')
        self.add(info)

        menu_item = menu.Menu('menu-wordpress', info.name,
                              info.short_description, info.icon_filename,
                              'wordpress:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-wordpress', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/wordpress/', clients=info.clients)
        self.add(shortcut)

        # Add php to avoid wordpress package bringing in lib-apache2-mod-php.
        # WordPress only supports MySQL/MariaDB as database server.
        packages = Packages(
            'packages-wordpress',
            [
                'wordpress',
                # Avoid WordPress package bringing in libapache2-mod-php
                'php',
                # Optional, for performance
                'php-imagick',
                # Optional, to upload plugins/themes using SSH connection
                'php-ssh2',
                # Optional, for performance
                'php-zip',
                # WordPress only supports MySQL/MariaDB as DB
                'default-mysql-server',
            ])
        self.add(packages)

        firewall = Firewall('firewall-wordpress', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-wordpress', 'wordpress-freedombox',
                              urls=['https://{host}/wordpress/'])
        self.add(webserver)

        daemon = Daemon('daemon-wordpress', 'wordpress-freedombox.timer')
        self.add(daemon)

        backup_restore = WordPressBackupRestore('backup-restore-wordpress',
                                                **manifest.backup)
        self.add(backup_restore)


class WordPressBackupRestore(BackupRestore):
    """Component to backup/restore WordPress."""

    def backup_pre(self, packet):
        """Save database contents."""
        super().backup_pre(packet)
        actions.superuser_run('wordpress', ['dump-database'])

    def restore_post(self, packet):
        """Restore database contents."""
        super().restore_post(packet)
        actions.superuser_run('wordpress', ['restore-database'])


def setup(helper, old_version=None):
    """Install and configure the module."""
    app.setup(old_version)
    helper.call('post', actions.superuser_run, 'wordpress', ['setup'])
    if not old_version:
        helper.call('post', app.enable)
