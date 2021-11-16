# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Transmission server.
"""

import json

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import add_user_to_share_group
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages

from . import manifest

version = 4

managed_services = ['transmission-daemon']

_description = [
    _('Transmission is a BitTorrent client with a web interface.'),
    _('BitTorrent is a peer-to-peer file sharing protocol. '
      'Note that BitTorrent is not anonymous.'),
    _('Please do not change the default port of the transmission daemon.'),
]

app = None

SYSTEM_USER = 'debian-transmission'


class TransmissionApp(app_module.App):
    """FreedomBox app for Transmission."""

    app_id = 'transmission'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {
            'bit-torrent': _('Download files using BitTorrent applications')
        }

        info = app_module.Info(
            app_id=self.app_id, version=version, name=_('Transmission'),
            icon_filename='transmission',
            short_description=_('BitTorrent Web Client'),
            description=_description, manual_page='Transmission',
            clients=manifest.clients,
            donation_url='https://transmissionbt.com/donate/')
        self.add(info)

        menu_item = menu.Menu('menu-transmission', info.name,
                              info.short_description, info.icon_filename,
                              'transmission:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-transmission', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            url='/transmission', clients=info.clients, login_required=True,
            allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-transmission', ['transmission-daemon'])
        self.add(packages)

        firewall = Firewall('firewall-transmission', info.name,
                            ports=['http', 'https',
                                   'transmission-client'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-transmission', 'transmission-plinth',
                              urls=['https://{host}/transmission'])
        self.add(webserver)

        daemon = Daemon(
            'daemon-transmission', managed_services[0], listen_ports=[
                (9091, 'tcp4'),
                (51413, 'tcp4'),
                (51413, 'tcp6'),
                (51413, 'udp4'),
            ])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-transmission',
                                          reserved_usernames=[SYSTEM_USER],
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-transmission',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    app.setup(old_version)

    if old_version and old_version <= 3 and app.is_enabled():
        app.get_component('firewall-transmission').enable()

    new_configuration = {
        'rpc-whitelist-enabled': False,
        'rpc-authentication-required': False
    }
    helper.call('post', actions.superuser_run, 'transmission',
                ['merge-configuration'],
                input=json.dumps(new_configuration).encode())
    add_user_to_share_group(SYSTEM_USER, managed_services[0])
    helper.call('post', app.enable)
