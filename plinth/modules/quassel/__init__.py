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
Plinth module for Quassel.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module
from plinth.utils import format_lazy

version = 1

depends = ['apps']

title = _('IRC Client (Quassel)')

description = [
    format_lazy(
        _('Quassel is an IRC application that is split into two parts, a '
          '"core" and a "client". This allows the core to remain connected '
          'to IRC servers, and to continue receiving messages, even when '
          'the client is disconnected. {box_name} can run the Quassel '
          'core service keeping you always online and one or more Quassel '
          'clients from a desktop or a mobile can be used to connect and '
          'disconnect from it.'), box_name=_(cfg.box_name)),

    _('You can connect to your Quassel core on the default Quassel port '
      '4242.  Clients to connect to Quassel from your '
      '<a href="http://quassel-irc.org/downloads">desktop</a> and '
      '<a href="http://quasseldroid.iskrembilen.com/">mobile</a> devices '
      'are available.')
]

service = None


def init():
    """Initialize the quassel module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-retweet', 'quassel:index', 730)

    global service
    service = service_module.Service(
        'quassel-plinth', title, is_external=True, enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['quassel-core'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current service status."""
    return {'enabled': is_enabled(),
            'is_running': is_running()}


def is_enabled():
    """Return whether the service is enabled."""
    return action_utils.service_is_enabled('quasselcore')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('quasselcore')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('quassel', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(4242, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(4242, 'tcp6'))

    return results
