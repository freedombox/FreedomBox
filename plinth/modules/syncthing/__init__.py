# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Syncthing.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['syncthing@syncthing']

managed_packages = ['syncthing']

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
          'users belonging to the "admin" or "syncthing" group.'),
        box_name=_(cfg.box_name)),
]

app = None


class SyncthingApp(app_module.App):
    """FreedomBox app for Syncthing."""

    app_id = 'syncthing'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        self.groups = {'syncthing': _('Administer Syncthing application')}

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Syncthing'), icon_filename='syncthing',
                               short_description=_('File Synchronization'),
                               description=_description,
                               manual_page='Syncthing', clients=clients)
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

        firewall = Firewall('firewall-syncthing-web', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        firewall = Firewall('firewall-syncthing-ports', info.name,
                            ports=['syncthing'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-syncthing', 'syncthing-plinth',
                              urls=['https://{host}/syncthing/'])
        self.add(webserver)

        daemon = Daemon('daemon-syncthing', managed_services[0])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-syncthing',
                                          groups=self.groups)
        self.add(users_and_groups)


def init():
    """Initialize the module."""
    global app
    app = SyncthingApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'syncthing', ['setup'])
    if not old_version:
        helper.call('post', app.enable)

    if old_version == 1 and app.is_enabled():
        app.get_component('firewall-syncthing-ports').enable()
