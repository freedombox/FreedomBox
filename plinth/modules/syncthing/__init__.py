# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure Syncthing."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import (Firewall,
                                                FirewallLocalProtection)
from plinth.modules.users import add_user_to_share_group
from plinth.modules.users import privileged as users_privileged
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_description = [
    _('Syncthing is an application to synchronize files across multiple '
      'devices, e.g. your desktop computer and mobile phone.  Creation, '
      'modification, or deletion of files on one device will be automatically '
      'replicated on all other devices that also run Syncthing.'),
    format_lazy(
        _('Running Syncthing on {box_name} provides an extra synchronization '
          'point for your data that is available most of the time, allowing '
          'your devices to synchronize more often.  {box_name} runs a single '
          'instance of Syncthing that may be used by multiple users.  Each '
          'user\'s set of devices may be synchronized with a distinct set of '
          'folders.  The web interface on {box_name} is only available for '
          'users belonging to the "admin" or "syncthing-access" group.'),
        box_name=_(cfg.box_name)),
]

SYSTEM_USER = 'syncthing'


class SyncthingApp(app_module.App):
    """FreedomBox app for Syncthing."""

    app_id = 'syncthing'

    _version = 6

    DAEMON = 'syncthing@syncthing'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        self.groups = {
            'syncthing-access': _('Administer Syncthing application')
        }

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Syncthing'), icon_filename='syncthing',
                               short_description=_('File Synchronization'),
                               description=_description,
                               manual_page='Syncthing',
                               clients=manifest.clients,
                               donation_url='https://syncthing.net/donations/')
        self.add(info)

        menu_item = menu.Menu('menu-syncthing', info.name,
                              info.short_description, info.icon_filename,
                              'syncthing:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-syncthing', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/syncthing/', clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(self.groups))
        self.add(shortcut)

        packages = Packages('packages-syncthing', ['syncthing'])
        self.add(packages)

        firewall = Firewall('firewall-syncthing-web', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall = Firewall('firewall-syncthing-ports', info.name,
                            ports=['syncthing'], is_external=True)
        self.add(firewall)

        firewall_local_protection = FirewallLocalProtection(
            'firewall-local-protection-syncthing', ['8384'])
        self.add(firewall_local_protection)

        webserver = Webserver('webserver-syncthing', 'syncthing-plinth',
                              urls=['https://{host}/syncthing/'])
        self.add(webserver)

        daemon = Daemon('daemon-syncthing', self.DAEMON)
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-syncthing',
                                          [SYSTEM_USER], self.groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-syncthing',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        add_user_to_share_group(SYSTEM_USER, SyncthingApp.DAEMON)

        if not old_version:
            self.enable()

        privileged.setup_config()

        if old_version == 1 and self.is_enabled():
            self.get_component('firewall-syncthing-ports').enable()

        if old_version and old_version <= 3:
            # rename LDAP and Django group
            old_groupname = 'syncthing'
            new_groupname = 'syncthing-access'

            users_privileged.rename_group(old_groupname, new_groupname)

            from django.contrib.auth.models import Group
            Group.objects.filter(name=old_groupname).update(name=new_groupname)

            # update web shares to have new group name
            from plinth.modules import sharing
            shares = sharing.list_shares()
            for share in shares:
                if old_groupname in share['groups']:
                    new_groups = share['groups']
                    new_groups.remove(old_groupname)
                    new_groups.append(new_groupname)

                    name = share['name']
                    sharing.remove_share(name)
                    sharing.add_share(name, share['path'], new_groups,
                                      share['is_public'])

    def uninstall(self):
        """De-configure and uninstall the app."""
        super().uninstall()
        privileged.uninstall()
