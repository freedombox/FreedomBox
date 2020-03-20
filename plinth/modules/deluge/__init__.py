# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure a Deluge web client.
"""

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

version = 6

managed_services = ['deluged', 'deluge-web']

managed_packages = ['deluged', 'deluge-web']

_description = [
    _('Deluge is a BitTorrent client that features a Web UI.'),
    _('The default password is \'deluge\', but you should log in and '
      'change it immediately after enabling this service.')
]

app = None

SYSTEM_USER = 'debian-deluged'


class DelugeApp(app_module.App):
    """FreedomBox app for Deluge."""

    app_id = 'deluge'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {
            'bit-torrent': _('Download files using BitTorrent applications')
        }

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Deluge'), icon_filename='deluge',
                               short_description=_('BitTorrent Web Client'),
                               description=_description, manual_page='Deluge',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-deluge', info.name, info.short_description,
                              info.icon_filename, 'deluge:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-deluge', info.name,
                                      short_description=info.short_description,
                                      url='/deluge', icon=info.icon_filename,
                                      clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        firewall = Firewall('firewall-deluge', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-deluge', 'deluge-plinth',
                              urls=['https://{host}/deluge'])
        self.add(webserver)

        daemon = Daemon('daemon-deluged', managed_services[0],
                        listen_ports=[(58846, 'tcp4')])
        self.add(daemon)

        daemon_web = Daemon('daemon-deluge-web', managed_services[1],
                            listen_ports=[(8112, 'tcp4')])
        self.add(daemon_web)

        users_and_groups = UsersAndGroups('users-and-groups-deluge',
                                          reserved_usernames=[SYSTEM_USER],
                                          groups=groups)
        self.add(users_and_groups)


def init():
    """Initialize the Deluge module."""
    global app
    app = DelugeApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'deluge', ['setup'])
    add_user_to_share_group(SYSTEM_USER)
    helper.call('post', app.enable)
