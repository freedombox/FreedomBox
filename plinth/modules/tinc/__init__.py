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
Plinth module to configure tinc.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module


version = 1

depends = ['apps']

service = None

managed_services = ['tinc@freedombox']

managed_packages = ['tinc']

title = _('Mesh VPN (tinc)')

description = [
    _('tinc is a Virtual Private Network (VPN). It uses tunnelling and '
      'encryption to create a secure private network between hosts on the '
      'Internet.'),

    _('tinc differs from traditional VPNs in that it uses a mesh network '
      'architecture, instead of a client-server model. In other words, any '
      'host can act as either client or server as needed.'),
]


def init():
    """Initialize the tinc module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-link', 'tinc:index')

    global service
    service = service_module.Service(
        managed_services[0], title, ports=['tinc'], is_external=True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', service.notify_enabled, None, True)


def is_setup():
    """Return whether tinc setup has been completed."""
    return actions.superuser_run('tinc', ['is-setup']).strip() == 'true'


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(655, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(655, 'tcp6'))

    results.append(action_utils.diagnose_port_listening(655, 'udp4'))
    results.append(action_utils.diagnose_port_listening(655, 'udp6'))

    return results
