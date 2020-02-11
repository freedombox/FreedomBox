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
Plinth module to configure coquelicot.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_services = ['coquelicot']

managed_packages = ['coquelicot']

_description = [
    _('Coquelicot is a "one-click" file sharing web application with a focus '
      'on protecting users\' privacy. It is best used for quickly sharing a '
      'single file. '),
    _('This Coquelicot instance is exposed to the public but requires an '
      'upload password to prevent unauthorized access. You can set a new '
      'upload password in the form that will appear below after installation. '
      'The default upload password is "test".')
]

app = None


class CoquelicotApp(app_module.App):
    """FreedomBox app for Coquelicot."""

    app_id = 'coquelicot'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Coquelicot'),
                               icon_filename='coquelicot',
                               short_description=_('File Sharing'),
                               description=_description,
                               manual_page='Coquelicot', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-coquelicot', info.name,
                              info.short_description, info.icon_filename,
                              'coquelicot:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-coquelicot', info.name,
                                      short_description=info.short_description,
                                      icon='coquelicot', url='/coquelicot',
                                      clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-coquelicot', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-coquelicot', 'coquelicot-freedombox',
                              urls=['https://{host}/coquelicot'])
        self.add(webserver)

        daemon = Daemon('daemon-coquelicot', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the module."""
    global app
    app = CoquelicotApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'coquelicot', ['setup'])
    helper.call('post', app.enable)


def get_current_max_file_size():
    """Get the current value of maximum file size."""
    size = actions.superuser_run('coquelicot', ['get-max-file-size'])
    return int(size.strip())
