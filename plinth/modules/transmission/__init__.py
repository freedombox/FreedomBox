# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Transmission server.
"""

import json

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import add_user_to_share_group
from plinth.modules.users.components import UsersAndGroups

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 3

managed_services = ['transmission-daemon']

managed_packages = ['transmission-daemon']

_description = [
    _('BitTorrent is a peer-to-peer file sharing protocol. '
      'Transmission daemon handles Bitorrent file sharing.  Note that '
      'BitTorrent is not anonymous.'),
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
            clients=clients, donation_url='https://transmissionbt.com/donate/')
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

        firewall = Firewall('firewall-transmission', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-transmission', 'transmission-plinth',
                              urls=['https://{host}/transmission'])
        self.add(webserver)

        daemon = Daemon('daemon-transmission', managed_services[0],
                        listen_ports=[(9091, 'tcp4')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-transmission',
                                          reserved_usernames=[SYSTEM_USER],
                                          groups=groups)
        self.add(users_and_groups)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)

    new_configuration = {
        'rpc-whitelist-enabled': False,
        'rpc-authentication-required': False
    }
    helper.call('post', actions.superuser_run, 'transmission',
                ['merge-configuration'],
                input=json.dumps(new_configuration).encode())
    add_user_to_share_group(SYSTEM_USER, managed_services[0])
    helper.call('post', app.enable)
