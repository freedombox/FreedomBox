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
Plinth module to configure Mumble server
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.views import ServiceView


version = 1

title = _('Voice Chat \n (Mumble)')

service = None

managed_services = ['mumble-server']

managed_packages = ['mumble-server']

description = [
    _('Mumble is an open source, low-latency, encrypted, high quality '
      'voice chat software.'),

    _('You can connect to your Mumble server on the regular Mumble port '
      '64738. <a href="http://mumble.info">Clients</a> to connect to Mumble '
      'from your desktop and Android devices are available.')
]

reserved_usernames = ['mumble-server']


def init():
    """Intialize the Mumble module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-headphones', 'mumble:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['mumble-plinth'],
            is_external=True,
            enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()


class MumbleServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "mumble"
    description = description


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['mumble-plinth'],
            is_external=True,
            enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('mumble', title,
                           details=description,
                           configure_url=reverse_lazy('mumble:index'),
                           login_required=False)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('mumble')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(64738, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp4'))
    results.append(action_utils.diagnose_port_listening(64738, 'udp6'))

    return results
