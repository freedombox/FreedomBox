# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for radicale.
"""

import logging

import augeas
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.config import DropinConfigs
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages, install
from plinth.utils import Version, format_lazy

from . import manifest, privileged

_description = [
    format_lazy(
        _('Radicale is a CalDAV and CardDAV server. It allows synchronization '
          'and sharing of scheduling and contact data. To use Radicale, a '
          '<a href="https://radicale.org/master.html#documentation/supported-'
          'clients">supported client application</a> is needed. Radicale can '
          'be accessed by any user with a {box_name} login.'),
        box_name=_(cfg.box_name)),
    _('Radicale provides a basic web interface, which only supports creating '
      'new calendars and addressbooks. It does not support adding events or '
      'contacts, which must be done using a separate client.'),
]

logger = logging.getLogger(__name__)

CONFIG_FILE = '/etc/radicale/config'


class RadicaleApp(app_module.App):
    """FreedomBox app for Radicale."""

    app_id = 'radicale'

    _version = 3

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Radicale'), icon_filename='radicale',
                               short_description=_('Calendar and Addressbook'),
                               description=_description,
                               manual_page='Radicale',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-radicale', info.name,
                              info.short_description, info.icon_filename,
                              'radicale:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-radicale', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/radicale/', clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        packages = Packages('packages-radicale', ['radicale'])
        self.add(packages)

        dropin_configs = DropinConfigs('dropin-configs-radicale', [
            '/etc/apache2/conf-available/radicale2-freedombox.conf',
        ])
        self.add(dropin_configs)

        firewall = Firewall('firewall-radicale', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-radicale', 'radicale2-freedombox',
                              urls=['https://{host}/radicale'])
        self.add(webserver)

        uwsgi = Uwsgi('uwsgi-radicale', 'radicale')
        self.add(uwsgi)

        users_and_groups = UsersAndGroups('users-and-groups-radicale',
                                          reserved_usernames=['radicale'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-radicale',
                                       **manifest.backup)
        self.add(backup_restore)

    def enable(self):
        """Fix missing directories before enabling radicale."""
        privileged.fix_paths()
        super().enable()

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()

    def force_upgrade(self, packages):
        """Force upgrade radicale to resolve conffile prompt."""
        if 'radicale' not in packages:
            return False

        # Allow upgrade from 2.* to newer 2.* and 3.*
        package = packages['radicale']
        if Version(package['new_version']) > Version('4~'):
            return False

        rights = get_rights_value()
        install(['radicale'], force_configuration='new')
        privileged.configure(rights)

        return True


def load_augeas():
    """Prepares the augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)

    # INI file lens
    aug.set('/augeas/load/Puppet/lens', 'Puppet.lns')
    aug.set('/augeas/load/Puppet/incl[last() + 1]', CONFIG_FILE)

    aug.load()
    return aug


def get_rights_value():
    """Returns the current Rights value."""
    aug = load_augeas()
    value = aug.get('/files' + CONFIG_FILE + '/rights/type')

    if value == 'from_file':
        # Default rights file is equivalent to owner_only.
        value = 'owner_only'

    return value
