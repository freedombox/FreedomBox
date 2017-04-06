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
Plinth module for service discovery.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import cfg
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy
from plinth.views import ServiceView

# pylint: disable=C0103

version = 1

is_essential = True

managed_services = ['avahi-daemon']

managed_packages = ['avahi-daemon']

title = _('Service Discovery')

description = [
    format_lazy(
        _('Service discovery allows other devices on the network to '
          'discover your {box_name} and services running on it.  It '
          'also allows {box_name} to discover other devices and '
          'services running on your local network.  Service discovery is '
          'not essential and works only on internal networks.  It may be '
          'disabled to improve security especially when connecting to a '
          'hostile local network.'), box_name=_(cfg.box_name))
]

service = None


def init():
    """Intialize the service discovery module."""
    menu = main_menu.get('system')
    menu.add_urlname(title, 'glyphicon-lamp', 'avahi:index')

    global service  # pylint: disable=W0603
    service = service_module.Service(
        managed_services[0], title, ports=['mdns'], is_external=False)


def setup(helper, old_version=False):
    """Install and configure the module."""
    helper.install(managed_packages)


class AvahiServiceView(ServiceView):
    service_id = managed_services[0]
    description = description
