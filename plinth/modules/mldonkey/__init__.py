# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for mldonkey.
"""

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import add_user_to_share_group
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.utils import format_lazy

from . import manifest

_description = [
    _('MLDonkey is a peer-to-peer file sharing application used to exchange '
      'large files. It can participate in multiple peer-to-peer networks '
      'including eDonkey, Kademlia, Overnet, BitTorrent and DirectConnect.'),
    _('Users belonging to admin and ed2k group can control it through the web '
      'interface. Users in the admin group can also control it through any of '
      'the separate mobile or desktop front-ends or a telnet interface. See '
      'manual.'),
    format_lazy(
        _('On {box_name}, downloaded files can be found in /var/lib/mldonkey/ '
          'directory.'), box_name=cfg.box_name)
]

_SYSTEM_USER = 'mldonkey'

app = None


class MLDonkeyApp(app_module.App):
    """FreedomBox app for MLDonkey."""

    app_id = 'mldonkey'

    _version = 2

    DAEMON = 'mldonkey-server'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'ed2k': _('Download files using eDonkey applications')}

        info = app_module.Info(
            app_id=self.app_id, version=self._version, name=_('MLDonkey'),
            icon_filename='mldonkey',
            short_description=_('Peer-to-peer File Sharing'),
            description=_description, manual_page='MLDonkey',
            clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-mldonkey', info.name,
                              info.short_description, info.icon_filename,
                              'mldonkey:index', parent_url_name='apps')
        self.add(menu_item)

        shortcuts = frontpage.Shortcut(
            'shortcut-mldonkey', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            url='/mldonkey/', login_required=True, clients=info.clients,
            allowed_groups=list(groups))
        self.add(shortcuts)

        packages = Packages('packages-mldonkey', ['mldonkey-server'])
        self.add(packages)

        firewall = Firewall('firewall-mldonkey', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-mldonkey', 'mldonkey-freedombox',
                              urls=['https://{host}/mldonkey/'])
        self.add(webserver)

        daemon = Daemon('daemon-mldonkey', self.DAEMON,
                        listen_ports=[(4080, 'tcp4')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-mldonkey',
                                          reserved_usernames=[_SYSTEM_USER],
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-mldonkey',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'mldonkey', ['pre-install'])
    app.setup(old_version)
    if not old_version:
        helper.call('post', app.enable)

    add_user_to_share_group(_SYSTEM_USER, MLDonkeyApp.DAEMON)
