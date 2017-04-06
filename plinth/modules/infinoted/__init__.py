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
Plinth module for infinoted.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy
from plinth.views import ServiceView


version = 1

service = None

managed_services = ['infinoted']

managed_packages = ['infinoted']

title = _('Gobby Server \n (infinoted)')

description = [
    _('infinoted is a server for Gobby, a collaborative text editor.'),

    format_lazy(
        _('To use it, <a href="https://gobby.github.io/">download Gobby</a>, '
          'desktop client and install it. Then start Gobby and select '
          '"Connect to Server" and enter your {box_name}\'s domain name.'),
        box_name=_(cfg.box_name)),
]


def init():
    """Initialize the infinoted module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-pencil', 'infinoted:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['infinoted-plinth'],
            is_external=True, enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()


class InfinotedServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "infinoted"
    description = description


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'infinoted', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['infinoted-plinth'],
            is_external=True, enable=enable, disable=disable)

    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('infinoted', title, url=None,
                           details=description,
                           configure_url=reverse_lazy('infinoted:index'),
                           login_required=False)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('infinoted')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(6523, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(6523, 'tcp6'))

    return results
