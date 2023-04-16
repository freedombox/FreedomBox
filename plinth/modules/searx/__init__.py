# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Searx."""

import os

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('Searx is a privacy-respecting Internet metasearch engine. '
      'It aggregrates and displays results from multiple search engines.'),
    _('Searx can be used to avoid tracking and profiling by search engines. '
      'It stores no cookies by default.')
]


class SearxApp(app_module.App):
    """FreedomBox app for Searx."""

    app_id = 'searx'

    _version = 5

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'web-search': _('Search the web')}

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('Searx'),
            icon_filename='searx', short_description=_('Web Search'),
            description=_description, manual_page='Searx',
            clients=manifest.clients,
            donation_url='https://searx.me/static/donate.html')
        self.add(info)

        menu_item = menu.Menu('menu-searx', info.name, info.short_description,
                              info.icon_filename, 'searx:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-searx', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            url='/searx/', clients=info.clients,
            login_required=(not is_public_access_enabled()),
            allowed_groups=list(groups))
        self.add(shortcut)

        # Include libjs-bootstrap to prevent accidental uninstall (see
        # issue #2298).
        packages = Packages('packages-searx', ['searx', 'libjs-bootstrap'])
        self.add(packages)

        firewall = Firewall('firewall-searx', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-searx', 'searx-freedombox',
                              urls=['https://{host}/searx/'])
        self.add(webserver)

        webserver = SearxWebserverAuth('webserver-searx-auth',
                                       'searx-freedombox-auth')
        self.add(webserver)

        uwsgi = Uwsgi('uwsgi-searx', 'searx')
        self.add(uwsgi)

        users_and_groups = UsersAndGroups('users-and-groups-searx',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-searx',
                                       **manifest.backup)
        self.add(backup_restore)

    def set_shortcut_login_required(self, login_required):
        """Change the login_required property of shortcut."""
        self.get_component('shortcut-searx').login_required = login_required

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version or old_version < 3:
            privileged.disable_public_access()
            self.enable()
            self.set_shortcut_login_required(True)

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.unininstall()


class SearxWebserverAuth(Webserver):
    """Component to handle Searx authentication webserver configuration."""

    def is_enabled(self):
        """Return if configuration is enabled or public access is enabled."""
        return is_public_access_enabled() or super().is_enabled()

    def enable(self):
        """Enable apache configuration only if public access is disabled."""
        if not is_public_access_enabled():
            super().enable()


def is_public_access_enabled():
    """Check whether public access is enabled for Searx."""
    return os.path.exists(manifest.PUBLIC_ACCESS_SETTING_FILE)


def enable_public_access():
    """Allow Searx app to be accessed by anyone with access."""
    privileged.enable_public_access()
    app = app_module.App.get('searx')
    app.get_component('webserver-searx-auth').disable()
    app.set_shortcut_login_required(False)


def disable_public_access():
    """Allow Searx app to be accessed by logged-in users only."""
    privileged.disable_public_access()
    app = app_module.App.get('searx')
    app.get_component('webserver-searx-auth').enable()
    app.set_shortcut_login_required(True)
