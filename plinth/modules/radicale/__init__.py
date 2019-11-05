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
FreedomBox app for radicale.
"""

import logging
import subprocess
from distutils.version import LooseVersion as LV

import augeas
from apt.cache import Cache
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['radicale']

managed_packages = ['radicale', 'uwsgi', 'uwsgi-plugin-python3']

name = _('Radicale')

icon_filename = 'radicale'

short_description = _('Calendar and Addressbook')

description = [
    format_lazy(
        _('Radicale is a CalDAV and CardDAV server. It allows synchronization '
          'and sharing of scheduling and contact data. To use Radicale, a '
          '<a href="http://radicale.org/clients/">supported client '
          'application</a> is needed. Radicale can be accessed by any user '
          'with a {box_name} login.'), box_name=_(cfg.box_name)),
    _('Radicale provides a basic web interface, which only supports creating '
      'new calendars and addressbooks. It does not support adding events or '
      'contacts, which must be done using a separate client.'),
]

clients = clients

reserved_usernames = ['radicale']

manual_page = 'Radicale'

logger = logging.getLogger(__name__)

CONFIG_FILE = '/etc/radicale/config'

VERSION_2 = LV('2')

app = None


class RadicaleApp(app_module.App):
    """FreedomBox app for Radicale."""

    app_id = 'radicale'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-radicale', name, short_description,
                              'radicale', 'radicale:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-radicale', name,
                                      short_description=short_description,
                                      icon=icon_filename, url='/radicale/',
                                      clients=clients, login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-radicale', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = RadicaleWebserver('webserver-radicale', None)
        self.add(webserver)

        uwsgi = RadicaleUwsgi('uwsgi-radicale', 'radicale')
        self.add(uwsgi)

        daemon = RadicaleDaemon('daemon-radicale', managed_services[0])
        self.add(daemon)


class RadicaleWebserver(Webserver):
    """Webserver enable/disable behavior specific for radicale."""

    @property
    def web_name(self):
        """Return web configuration name based on radicale version."""
        current_version = get_package_version()
        if current_version and current_version < VERSION_2:
            return 'radicale-plinth'

        return 'radicale2-freedombox'

    @web_name.setter
    def web_name(self, web_name):
        """Set the web name"""


class RadicaleUwsgi(Uwsgi):
    """uWSGI enable/disable behavior specific for radicale."""

    def is_enabled(self):
        """Return whether the uWSGI configuration is enabled if version>=2."""
        package_version = get_package_version()
        if package_version and package_version >= VERSION_2:
            return super().is_enabled()

        return True

    def enable(self):
        """Enable the uWSGI configuration if version >=2."""
        package_version = get_package_version()
        if package_version and package_version >= VERSION_2:
            actions.superuser_run('radicale', ['fix-collections'])
            super().enable()

    def disable(self):
        """Disable the uWSGI configuration if version >=2."""
        package_version = get_package_version()
        if package_version and package_version >= VERSION_2:
            super().disable()


class RadicaleDaemon(Daemon):
    """Daemon enable/disable behavior specific for radicale."""

    @staticmethod
    def _is_old_radicale():
        """Return whether radicale is less than version 2."""
        package_version = get_package_version()
        return package_version and package_version < VERSION_2

    def is_enabled(self):
        """Return whether daemon is enabled if version < 2."""
        if self._is_old_radicale():
            return super().is_enabled()

        return True

    def enable(self):
        """Enable the daemon if version < 2."""
        if self._is_old_radicale():
            super().enable()
        else:
            super().disable()

    def disable(self):
        """Disable the daemon if version < 2."""
        if self._is_old_radicale():
            super().disable()

    def is_running(self):
        """Return whether daemon is enabled if version < 2."""
        if self._is_old_radicale():
            return super().is_running()

        return True


def init():
    """Initialize the radicale module."""
    global app
    app = RadicaleApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    if old_version == 1:
        # Check that radicale 2.x is available for install.
        cache = Cache()
        candidate = cache['radicale'].candidate
        if candidate < '2':
            logger.error('Radicale 2.x is not available to install.')

        # Try to upgrade radicale 1.x to 2.x.
        helper.call('pre', actions.superuser_run, 'radicale', ['migrate'])
        helper.install(managed_packages, force_configuration='new')

        # Check that radicale 2.x is installed.
        current_version = get_package_version()
        if not current_version:
            logger.error('Could not determine installed version of radicale.')
        elif current_version < VERSION_2:
            logger.error('Could not install radicale 2.x.')

        # Enable radicale.
        helper.call('post', actions.superuser_run, 'radicale', ['setup'])
    else:
        helper.install(managed_packages)
        helper.call('post', actions.superuser_run, 'radicale', ['setup'])

    helper.call('post', app.enable)


def get_package_version():
    try:
        proc = subprocess.run(['radicale', '--version'],
                              stdout=subprocess.PIPE, check=True)
        output = proc.stdout.decode('utf-8')
    except subprocess.CalledProcessError:
        return None

    package_version = str(output.strip())
    return LV(package_version)


def enable():
    """Enable the module."""
    actions.superuser_run('radicale', ['enable'])
    app.enable()


def disable():
    """Disable the module."""
    actions.superuser_run('radicale', ['disable'])
    app.disable()


def load_augeas():
    """Prepares the augeas."""
    aug = augeas.Augeas(
        flags=augeas.Augeas.NO_LOAD + augeas.Augeas.NO_MODL_AUTOLOAD)

    # INI file lens
    aug.set('/augeas/load/Puppet/lens', 'Puppet.lns')
    aug.set('/augeas/load/Puppet/incl[last() + 1]', CONFIG_FILE)

    aug.load()
    return aug


def get_rights_value():
    """Returns the current Rights value."""
    aug = load_augeas()
    value = aug.get('/files' + CONFIG_FILE + '/rights/type')

    current_version = get_package_version()
    if current_version and current_version >= VERSION_2:
        if value == 'from_file':
            # Radicale 2.x default rights file is equivalent to owner_only.
            value = 'owner_only'

    return value


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/radicale',
                                         check_certificate=False))

    return results
