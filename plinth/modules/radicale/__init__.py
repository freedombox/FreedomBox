# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for radicale.
"""

import logging
import subprocess
from distutils.version import LooseVersion as LV

import augeas
from apt.cache import Cache
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Uwsgi, Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.utils import format_lazy, Version

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['radicale']

managed_packages = ['radicale', 'uwsgi', 'uwsgi-plugin-python3']

_description = [
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
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Radicale'), icon_filename='radicale',
                               short_description=_('Calendar and Addressbook'),
                               description=_description,
                               manual_page='Radicale', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-radicale', info.name,
                              info.short_description, info.icon_filename,
                              'radicale:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-radicale', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/radicale/', clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-radicale', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = RadicaleWebserver('webserver-radicale', None,
                                      urls=['https://{host}/radicale'])
        self.add(webserver)

        uwsgi = RadicaleUwsgi('uwsgi-radicale', 'radicale')
        self.add(uwsgi)

        daemon = RadicaleDaemon('daemon-radicale', managed_services[0])
        self.add(daemon)

        users_and_groups = UsersAndGroups('users-and-groups-radicale',
                                          reserved_usernames=['radicale'])
        self.add(users_and_groups)


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


def force_upgrade(helper, packages):
    """Force upgrade radicale to resolve conffile prompt."""
    if 'radicale' not in packages:
        return False

    # Allow upgrade from 2.* to newer 2.*
    current_version = get_package_version()
    if not current_version or current_version < VERSION_2:
        return False

    package = packages['radicale']
    if Version(package['new_version']) > Version('3~'):
        return False

    rights = get_rights_value()
    helper.install(['radicale'], force_configuration='new')
    actions.superuser_run('radicale', ['configure', '--rights_type', rights])

    return True


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
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)

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
