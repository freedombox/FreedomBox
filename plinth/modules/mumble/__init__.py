# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Mumble server.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_services = ['mumble-server']

managed_packages = ['mumble-server']

_description = [
    _('Mumble is an open source, low-latency, encrypted, high quality '
      'voice chat software.'),
    _('You can connect to your Mumble server on the regular Mumble port '
      '64738. <a href="http://mumble.info">Clients</a> to connect to Mumble '
      'from your desktop and Android devices are available.')
]

app = None


class MumbleApp(app_module.App):
    """FreedomBox app for Mumble."""

    app_id = 'mumble'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Mumble'), icon_filename='mumble',
                               short_description=_('Voice Chat'),
                               description=_description, manual_page='Mumble',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-mumble', info.name, info.short_description,
                              'mumble', 'mumble:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-mumble', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('mumble:index'), clients=info.clients)
        self.add(shortcut)

        firewall = Firewall('firewall-mumble', info.name,
                            ports=['mumble-plinth'], is_external=True)
        self.add(firewall)

        daemon = Daemon(
            'daemon-mumble', managed_services[0],
            listen_ports=[(64738, 'tcp4'), (64738, 'tcp6'), (64738, 'udp4'),
                          (64738, 'udp6')])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-mumble',
                                          reserved_usernames=['mumble-server'])
        self.add(users_and_groups)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
