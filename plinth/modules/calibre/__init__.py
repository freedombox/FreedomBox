# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for calibre e-book library."""

import re

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    format_lazy(
        _('calibre server provides online access to your e-book collection. '
          'You can store your e-books on your {box_name}, read them online or '
          'from any of your devices.'), box_name=_(cfg.box_name)),
    _('You can organize your e-books, extract and edit their metadata, and '
      'perform advanced search. calibre can import, export, or convert across '
      'a wide range of formats to make e-books ready for reading on any '
      'device. It also provides an online web reader. It remembers your '
      'last read location, bookmarks, and highlighted text. Content '
      'distribution using OPDS is currently not supported.'),
    _('Only users belonging to <em>calibre</em> group will be able to access '
      'the app. All users with access can use all the libraries.')
]

LIBRARY_NAME_PATTERN = r'[a-zA-Z0-9 _-]+'


class CalibreApp(app_module.App):
    """FreedomBox app for calibre."""

    app_id = 'calibre'

    _version = 2

    DAEMON = 'calibre-server-freedombox'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'calibre': _('Use calibre e-book libraries')}

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('calibre'), icon_filename='calibre',
                               short_description=_('E-book Library'),
                               description=_description, manual_page='Calibre',
                               clients=manifest.clients,
                               donation_url='https://calibre-ebook.com/donate')
        self.add(info)

        menu_item = menu.Menu('menu-calibre', info.name,
                              info.short_description, info.icon_filename,
                              'calibre:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-calibre', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/calibre',
                                      clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-calibre', ['calibre'])
        self.add(packages)

        firewall = Firewall('firewall-calibre', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-calibre', ['8844'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-calibre', 'calibre-freedombox',
                              urls=['https://{host}/calibre'])
        self.add(webserver)

        daemon = Daemon('daemon-calibre', self.DAEMON,
                        listen_ports=[(8844, 'tcp4')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-calibre',
                                          reserved_usernames=['calibre'],
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-calibre',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()


def validate_library_name(library_name):
    """Raise exception if library name does not fit the accepted pattern."""
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', library_name):
        raise Exception('Invalid library name')
