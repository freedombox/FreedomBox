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
Plinth module for repro.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import service as service_module

version = 1

depends = ['apps']

title = _('SIP Server (repro)')

description = [
    _('repro provides various SIP services that a SIP softphone can utilize '
      'to provide audio and video calls as well as presence and instant '
      'messaging. repro provides a server and SIP user accounts that clients '
      'can use to let their presence known.  It also acts as a proxy to '
      'federate SIP communications to other servers on the Internet similar '
      'to email.'),

    _('To make SIP calls, a client application is needed. Available clients '
      'include <a href="https://jitsi.org/">Jitsi</a> (for computers) and '
      '<a href="https://f-droid.org/repository/browse/?fdid=com.csipsimple"> '
      'CSipSimple</a> (for Android phones).'),

    _('<strong>Note:</strong>  Before using repro, domains and users will '
      'need to be configured using the <a href="/repro/domains.html">'
      'web-based configuration panel</a>. Users in the <em>admin</em> group '
      'will be able to log in to the repro configuration panel. After setting '
      'the domain, it is required to restart the repro service. Disable the '
      'service and re-enable it.'),
]

service = None


def init():
    """Initialize the repro module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-phone-alt', 'repro:index', 825)

    global service
    service = service_module.Service(
        'repro', title, ['sip-plinth', 'sip-tls-plinth'], is_external=True,
        enabled=is_enabled())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(['repro'])
    helper.call('post', actions.superuser_run, 'repro', ['setup'])
    helper.call('post', service.notify_enabled, None, True)


def get_status():
    """Get the current service status."""
    return {'enabled': is_enabled(),
            'is_running': is_running()}


def is_enabled():
    """Return whether the service is enabled."""
    return action_utils.service_is_enabled('repro')


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('repro')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('repro', [sub_command])
    service.notify_enabled(None, should_enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(5060, 'udp4'))
    results.append(action_utils.diagnose_port_listening(5060, 'udp6'))
    results.append(action_utils.diagnose_port_listening(5060, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5060, 'tcp6'))
    results.append(action_utils.diagnose_port_listening(5061, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(5061, 'tcp6'))

    return results
