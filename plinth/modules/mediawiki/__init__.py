# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure MediaWiki."""

import re
from urllib.parse import urlparse

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('MediaWiki is the wiki engine that powers Wikipedia and other WikiMedia '
      'projects. A wiki engine is a program for creating a collaboratively '
      'edited website. You can use MediaWiki to host a wiki-like website, '
      'take notes or collaborate with friends on projects.'),
    _('This MediaWiki instance comes with a randomly generated administrator '
      'password. You can set a new password in the "Configuration" section '
      'and log in using the "admin" account. You can then create more user '
      'accounts from MediaWiki itself by going to the <a '
      'href="/mediawiki/index.php/Special:CreateAccount">'
      'Special:CreateAccount</a> page.'),
    _('Anyone with a link to this wiki can read it. Only users that are '
      'logged in can make changes to the content.')
]

STATIC_CONFIG_FILE = '/etc/mediawiki/FreedomBoxStaticSettings.php'
USER_CONFIG_FILE = '/etc/mediawiki/FreedomBoxSettings.php'


class MediaWikiApp(app_module.App):
    """FreedomBox app for MediaWiki."""

    app_id = 'mediawiki'

    _version = 10

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        self._private_mode = True

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('MediaWiki'), icon_filename='mediawiki',
                               short_description=_('Wiki'),
                               description=_description,
                               manual_page='MediaWiki',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-mediawiki', info.name,
                              info.short_description, info.icon_filename,
                              'mediawiki:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = Shortcut('shortcut-mediawiki', info.name,
                            short_description=info.short_description,
                            icon=info.icon_filename, url='/mediawiki',
                            clients=info.clients, login_required=True)
        self.add(shortcut)

        packages = Packages('packages-mediawiki',
                            ['mediawiki', 'imagemagick', 'php-sqlite3'])
        self.add(packages)

        firewall = Firewall('firewall-mediawiki', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-mediawiki', 'mediawiki',
                              urls=['https://{host}/mediawiki/'],
                              expect_redirects=True)
        self.add(webserver)

        webserver = Webserver('webserver-mediawiki-freedombox',
                              'mediawiki-freedombox')
        self.add(webserver)

        daemon = Daemon('daemon-mediawiki', 'mediawiki-jobrunner')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-mediawiki',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        privileged.update()
        self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


class Shortcut(frontpage.Shortcut):
    """Frontpage shortcut for only logged users when in private mode."""

    def enable(self):
        """When enabled, check if MediaWiki is in private mode."""
        super().enable()
        self.login_required = privileged.private_mode('status')


def _get_config_value_in_file(setting_name, config_file):
    """Return the value of a setting from a config file."""
    with open(config_file, 'r', encoding='utf-8') as config:
        for line in config:
            if line.startswith(setting_name):
                return re.findall(r'["\'][^"\']*["\']', line)[0].strip('"\'')

        return None


def _get_config_value(setting_name):
    """Return a configuration value from multiple configuration files."""
    return _get_config_value_in_file(setting_name, USER_CONFIG_FILE) or \
        _get_config_value_in_file(setting_name, STATIC_CONFIG_FILE)


def get_default_skin():
    """Return the value of the default skin."""
    return _get_config_value('$wgDefaultSkin')


def get_server_url():
    """Return the value of the server URL."""
    server_url = _get_config_value('$wgServer')
    return urlparse(server_url).netloc


def set_server_url(domain):
    """Set the value of $wgServer."""
    protocol = 'https'
    if domain.endswith('.onion'):
        protocol = 'http'

    privileged.set_server_url(f'{protocol}://{domain}')


def get_site_name():
    """Return the value of MediaWiki's site name."""
    return _get_config_value('$wgSitename') or 'Wiki'


def get_default_language():
    """Return the value of MediaWiki's default language"""
    return _get_config_value('$wgLanguageCode') or None
