# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for bepasty."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.config import DropinConfigs
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages

from . import manifest, privileged

_description = [
    _('bepasty is a web application that allows large files to be uploaded '
      'and shared. Text and code snippets can also be pasted and shared. '
      'Text, image, audio, video and PDF documents can be previewed in the '
      'browser. Shared files can be set to expire after a time period.'),
    _('bepasty does not use usernames for login. It only uses passwords. For '
      'each password, a set of permissions can be selected. Once you have '
      'created a password, you can share it with the users who should have the'
      ' associated permissions.'),
    _('You can also create multiple passwords with the same set of privileges,'
      ' and distribute them to different people or groups. This will allow '
      'you to later revoke access for a single person or group, by removing '
      'their password from the list.'),
]

PERMISSIONS = {
    'read': _('Read a file, if a web link to the file is available'),
    'create': _('Create or upload files'),
    'list': _('List all files and their web links'),
    'delete': _('Delete files'),
    'admin': _('Administer files: lock/unlock files'),
}

DEFAULT_PERMISSIONS = {
    '': _('None, password is always required'),
    'read': _('Read a file, if a web link to the file is available'),
    'read list': _('List and read all files'),
}


class BepastyApp(app_module.App):
    """FreedomBox app for bepasty."""

    app_id = 'bepasty'

    _version = 3

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(self.app_id, self._version, name=_('bepasty'),
                               icon_filename='bepasty',
                               description=_description, manual_page='bepasty',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-bepasty', info.name,
                              info.short_description, info.icon_filename,
                              'bepasty:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-bepasty', info.name,
                                      info.short_description,
                                      info.icon_filename, '/bepasty',
                                      clients=manifest.clients)
        self.add(shortcut)

        packages = Packages('packages-bepasty', ['bepasty'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-bepasty', [
            '/etc/apache2/conf-available/bepasty-freedombox.conf',
            '/etc/uwsgi/apps-available/bepasty-freedombox.ini'
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-bepasty', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        uwsgi = Uwsgi('uwsgi-bepasty', 'bepasty-freedombox')
        self.add(uwsgi)

        webserver = Webserver('webserver-bepasty', 'bepasty-freedombox',
                              urls=['https://{host}/bepasty/'])
        self.add(webserver)

        backup_restore = BackupRestore('backup-restore-bepasty',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup('freedombox.local')
        if not old_version:
            self.enable()

        if old_version == 1 and not privileged.get_configuration().get(
                'DEFAULT_PERMISSIONS'):
            # Upgrade to a better default only if user hasn't changed the
            # value.
            privileged.set_default(['read'])

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()
