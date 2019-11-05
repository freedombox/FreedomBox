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
FreedomBox app for mldonkey.
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

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_services = ['mldonkey-server']

managed_packages = ['mldonkey-server']

name = _('MLDonkey')

icon_filename = 'mldonkey'

short_description = _('Peer-to-peer File Sharing')

description = [
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

clients = clients

reserved_usernames = ['mldonkey']

group = ('ed2k', _('Download files using eDonkey applications'))

manual_page = 'MLDonkey'

app = None


class MLDonkeyApp(app_module.App):
    """FreedomBox app for MLDonkey."""

    app_id = 'mldonkey'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-mldonkey', name, short_description,
                              'mldonkey', 'mldonkey:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcuts = frontpage.Shortcut(
            'shortcut-mldonkey', name, short_description=short_description,
            icon=icon_filename, url='/mldonkey/', login_required=True,
            clients=clients, allowed_groups=[group[0]])
        self.add(shortcuts)

        firewall = Firewall('firewall-mldonkey', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-mldonkey', 'mldonkey-freedombox')
        self.add(webserver)

        daemon = Daemon('daemon-mldonkey', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the MLDonkey module."""
    global app
    app = MLDonkeyApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'mldonkey', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(4080, 'tcp4'))
    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/mldonkey/',
                                         check_certificate=False))

    return results
