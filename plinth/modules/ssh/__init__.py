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
FreedomBox app for OpenSSH server.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.views import ServiceView

from .manifest import backup

version = 1

is_essential = True

managed_services = ['ssh']

managed_packages = ['openssh-server']

name = _('Secure Shell (SSH) Server')

description = [
    _('A Secure Shell server uses the secure shell protocol to accept '
      'connections from remote computers. An authorized remote computer '
      'can perform administration tasks, copy files or run other services '
      'using such connections.')
]

service = None


def init():
    """Intialize the ssh module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-console', 'ssh:index')

    global service
    service = service_module.Service(
        managed_services[0], name, ports=['ssh'], is_external=True)


def setup(helper, old_version=None):
    """Configure the module."""
    actions.superuser_run('ssh', ['setup'])


class SshServiceView(ServiceView):
    service_id = managed_services[0]
    description = description
