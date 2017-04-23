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
Plinth module to configure OpenVPN server.
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


version = 1

service = None

managed_services = ['openvpn@freedombox']

managed_packages = ['openvpn', 'easy-rsa']

title = _('Virtual Private Network \n (OpenVPN)')

description = [
    format_lazy(
        _('Virtual Private Network (VPN) is a technique for securely '
          'connecting two devices in order to access resources of a '
          'private network.  While you are away from home, you can connect '
          'to your {box_name} in order to join your home network and '
          'access private/internal services provided by {box_name}. '
          'You can also access the rest of the Internet via {box_name} '
          'for added security and anonymity.'), box_name=_(cfg.box_name))
]


def init():
    """Initialize the OpenVPN module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-lock', 'openvpn:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['openvpn'], is_external=True)

        if service.is_enabled() and is_setup():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['openvpn'], is_external=True,
            enable=enable, disable=disable)


def add_shortcut():
    """Add shortcut in frontpage."""
    download_profile = \
        format_lazy(_('<a class="btn btn-primary btn-sm" href="{link}">'
                      'Download Profile</a>'),
                    link=reverse_lazy('openvpn:profile'))
    frontpage.add_shortcut('openvpn', title,
                           details=description + [download_profile],
                           configure_url=reverse_lazy('openvpn:index'),
                           login_required=True)


def is_setup():
    """Return whether the service is running."""
    return actions.superuser_run('openvpn', ['is-setup']).strip() == 'true'


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('openvpn')


def diagnose():
    """Run diagnostics and return the results."""
    return [action_utils.diagnose_port_listening(1194, 'udp4')]
