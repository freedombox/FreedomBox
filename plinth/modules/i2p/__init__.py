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
FreedomBox app to configure I2P.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.modules.users import register_group
from .manifest import backup, clients

version = 1

servicename = 'i2p'

managed_services = [servicename]

managed_packages = ['i2p']

name = _('I2P')

short_description = _('Anonymity Network')

description = [
    _('I2P is an anonymous overlay network - a network within a network. '
      'It is intended to protect communication from dragnet surveillance '
      'and monitoring by third parties such as ISPs. '),
    _('When enabled, I2P\'s web interface will be available from '
      '<a href="/i2p/">/i2p</a>.'),
]

clients = clients

group = ('i2p', _('Manage I2P application'))

service = None

manual_page = 'I2P'


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'i2p', 'i2p:index',
                     short_description)
    register_group(group)

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

    helper.install(managed_packages)
    helper.call('post', action_utils.webserver_enable, "proxy_html", kind="module")
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
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut('i2p', name,
                           short_description=short_description,
                           url='/i2p/', login_required=True,
                           allowed_groups=[group[0]])


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running("i2p")


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled("i2p") and action_utils.webserver_is_enabled("i2p-plinth")


def enable():
    """Enable the module."""
    actions.superuser_run("i2p", ["enable"])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run("i2p", ["disable"])
    frontpage.remove_shortcut('i2p')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/i2p/',
                                         check_certificate=False))

    return results
