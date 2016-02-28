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

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.utils import format_lazy


version = 1

depends = ['apps']

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

service = None


def init():
    """Initialize the radicale module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-calendar', 'radicale:index', 375)

    global service
    service = service_module.Service(
        'radicale', title, ['http', 'https'], is_external=True,
        enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['radicale'])
    helper.call('post', actions.superuser_run, 'radicale', ['setup'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current service status."""
    return {'enabled': is_enabled(),
            'is_running': is_running()}


def is_enabled():
    """Return whether the service is enabled."""
    return action_utils.service_is_enabled('radicale')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('radicale')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('radicale', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(5232, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5232, 'tcp6'))
    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/radicale', extra_options=['--no-check-certificate']))

    return results
