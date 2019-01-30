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

import subprocess
from distutils.version import LooseVersion as LV

from apt.cache import Cache
import augeas
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, cfg, frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

service = None

managed_services = ['radicale']

managed_packages = ['radicale', 'uwsgi', 'uwsgi-plugin-python3']

name = _('Radicale')

short_description = _('Calendar and Addressbook')

description = [
    format_lazy(
        _('Radicale is a CalDAV and CardDAV server. It allows synchronization '
          'and sharing of scheduling and contact data. To use Radicale, a '
          '<a href="http://radicale.org/clients/">supported client '
          'application</a> is needed. Radicale can be accessed by any user '
          'with a {box_name} login.'), box_name=_(cfg.box_name)),
]

clients = clients

reserved_usernames = ['radicale']

manual_page = 'Radicale'

CONFIG_FILE = '/etc/radicale/config'

VERSION_2 = LV('2')


def init():
    """Initialize the radicale module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'radicale', 'radicale:index', short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    if old_version == 1:
        # Check that radicale 2.x is available for install.
        cache = Cache()
        candidate = cache['radicale'].candidate
        if candidate < '2':
            raise RuntimeError('Radicale 2.x is not available to install.')

        # Try to upgrade radicale 1.x to 2.x.
        helper.call('pre', actions.superuser_run, 'radicale', ['migrate'])
        helper.install(managed_packages)

        # Check that radicale 2.x is installed.
        current_version = get_package_version()
        if not current_version:
            raise RuntimeError(
                'Could not determine installed version of radicale.')
        elif current_version < VERSION_2:
            raise RuntimeError('Could not install radicale 2.x.')

        # Enable radicale.
        helper.call('post', actions.superuser_run, 'radicale', ['setup'])
    else:
        helper.install(managed_packages)
        helper.call('post', actions.superuser_run, 'radicale', ['setup'])

    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut(
        'radicale', name, short_description=short_description,
        details=description, configure_url=reverse_lazy('radicale:index'),
        login_required=True)


def get_package_version():
    try:
        proc = subprocess.run(['radicale', '--version'],
                              stdout=subprocess.PIPE, check=True)
        output = proc.stdout.decode('utf-8')
    except subprocess.CalledProcessError:
        return None

    package_version = str(output.strip())
    return LV(package_version)


def get_web_config(current_version=None):
    """Return the name of the webserver configuration based on version."""
    if current_version is None:
        current_version = get_package_version()

    if current_version and current_version < VERSION_2:
        return 'radicale-plinth'

    return 'radicale2-freedombox'


def is_running():
    """Return whether the service is running."""
    if get_package_version() < VERSION_2:
        return action_utils.service_is_running('radicale')

    return action_utils.service_is_running('uwsgi') \
        and action_utils.uwsgi_is_enabled('radicale')


def is_enabled():
    """Return whether the module is enabled."""
    package_version = get_package_version()
    if package_version >= VERSION_2:
        daemon_enabled = action_utils.uwsgi_is_enabled('radicale')
    else:
        daemon_enabled = action_utils.service_is_enabled('radicale')

    return (action_utils.webserver_is_enabled(get_web_config(package_version))
            and daemon_enabled)


def enable():
    """Enable the module."""
    actions.superuser_run('radicale', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('radicale', ['disable'])
    frontpage.remove_shortcut('radicale')


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

    results.append(action_utils.diagnose_port_listening(5232, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5232, 'tcp6'))
    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/radicale',
                                         check_certificate=False))

    return results
