#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app to configure Syncthing.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

managed_services = ['syncthing@syncthing']

managed_packages = ['syncthing']

name = _('Syncthing')

short_description = _('File Synchronization')

description = [
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
          'users belonging to the "admin" group.'), box_name=_(cfg.box_name)),
    _('When enabled, Syncthing\'s web interface will be available from '
      '<a href="/syncthing/">/syncthing</a>.  Desktop and mobile clients are '
      'also <a href="https://syncthing.net/">available</a>.'),
]

clients = clients

group = ('syncthing', _('Administer Syncthing application'))

manual_page = 'Syncthing'

app = None


class SyncthingApp(app_module.App):
    """FreedomBox app for Syncthing."""

    app_id = 'syncthing'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-syncthing', name, short_description,
                              'syncthing', 'syncthing:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-syncthing', name, short_description=short_description,
            icon='syncthing', url='/syncthing/', clients=clients,
            login_required=True, allowed_groups=[group[0]])
        self.add(shortcut)

        firewall = Firewall('firewall-syncthing', name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-syncthing', 'syncthing-plinth')
        self.add(webserver)

        daemon = Daemon('daemon-syncthing', managed_services[0])
        self.add(daemon)


def init():
    """Intialize the module."""
    global app
    app = SyncthingApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'syncthing', ['setup'])
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/syncthing/',
                                         check_certificate=False))

    return results
