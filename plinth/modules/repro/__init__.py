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

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.views import ServiceView

version = 2

managed_services = ['repro']

managed_packages = ['repro']

title = _('SIP Server \n (repro)')

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

reserved_usernames = ['repro']

service = None


def init():
    """Initialize the repro module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-phone-alt', 'repro:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title,
            ports=['sip', 'sips', 'rtp-plinth'],
            is_external=True, enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()


class ReproServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "repro"
    description = description


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'repro', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title,
            ports=['sip', 'sips', 'rtp-plinth'],
            is_external=True, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('repro', title,
                           details=description,
                           configure_url=reverse_lazy('repro:index'),
                           login_required=True)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('repro')


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
