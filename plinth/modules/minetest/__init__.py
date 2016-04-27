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
Plinth module for minetest.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.utils import format_lazy
from plinth.views import ServiceView


version = 1

depends = ['apps']

service = None

managed_services = ['minetest-server']

title = _('Block Sandbox (Minetest)')

description = [
    format_lazy(
        _('Minetest is a multiplayer infinite-world block sandbox. This '
          'module enables the Minetest server to be run on this '
          '{box_name}, on the default port (30000). To connect to the server, '
          'a <a href="http://www.minetest.net/downloads/">Minetest client</a> '
          'is needed.'), box_name=_(cfg.box_name)),
]

def init():
    """Initialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-th-large', 'minetest:index', 325)

    global service
    service = service_module.Service(
        managed_services[0], title, is_external=True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_services)
    helper.call('post', service.notify_enabled, None, True)


class MinetestServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "minetest"
    description = description
    show_status_block = False


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(30000, 'udp4'))

    return results
