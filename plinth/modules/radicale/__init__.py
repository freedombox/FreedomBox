#
# This file is part of Plinth.
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
Plinth module for radicale.
"""

import augeas
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.utils import format_lazy

version = 1

depends = ['apps']

service = None

managed_services = ['radicale']

managed_packages = ['radicale']

title = _('Calendar and Addressbook (Radicale)')

description = [
    format_lazy(
        _('Radicale is a CalDAV and CardDAV server. It allows synchronization '
          'and sharing of scheduling and contact data. To use Radicale, a '
          '<a href="http://radicale.org/user_documentation/'
          '#idcaldav-and-carddav-clients"> supported client application</a> '
          'is needed. Radicale can be accessed by any user with a {box_name} '
          'login.'), box_name=_(cfg.box_name)),
]

CONFIG_FILE = '/etc/radicale/config'


def init():
    """Initialize the radicale module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-calendar', 'radicale:index')

    global service
    service = service_module.Service(
        managed_services[0], title, ports=['http', 'https'], is_external=True,
        enable=enable, disable=disable)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'radicale', ['setup'])
    helper.call('post', service.notify_enabled, None, True)


def enable():
    """Enable the module."""
    actions.superuser_run('radicale', ['enable'])


def disable():
    """Disable the module."""
    actions.superuser_run('radicale', ['disable'])


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
    return value


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(5232, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5232, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/radicale', check_certificate=False))

    return results
