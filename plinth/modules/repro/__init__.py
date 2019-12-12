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
FreedomBox app for repro.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.views import AppView

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['repro']

managed_packages = ['repro']

name = _('repro')

short_description = _('SIP Server')

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
      'need to be configured using the <a href="/repro/domains.html" '
      'data-turbolinks="false">web-based configuration panel</a>. Users in '
      'the <em>admin</em> group will be able to log in to the repro '
      'configuration panel. After setting the domain, it is required to '
      'restart the repro service. Disable the service and re-enable it.'),
]

clients = clients

reserved_usernames = ['repro']

manual_page = 'Repro'

port_forwarding_info = [('UDP', '1024-65535')]

app = None


class ReproApp(app_module.App):
    """FreedomBox app for Repro."""

    app_id = 'repro'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-repro', name, short_description, 'repro',
                              'repro:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-repro', name, short_description=short_description,
            icon='repro', description=description,
            configure_url=reverse_lazy('repro:index'), clients=clients,
            login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-repro', name,
                            ports=['sip', 'sips',
                                   'rtp-plinth'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-repro', 'repro-plinth')
        self.add(webserver)

        daemon = Daemon(
            'daemon-repro', managed_services[0], listen_ports=[(5060, 'udp4'),
                                                               (5060, 'udp6'),
                                                               (5060, 'tcp4'),
                                                               (5060, 'tcp6'),
                                                               (5061, 'tcp4'),
                                                               (5061, 'tcp6')])
        self.add(daemon)


def init():
    """Initialize the repro module."""
    global app
    app = ReproApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


class ReproAppView(AppView):
    clients = clients
    name = name
    description = description
    diagnostics_module_name = 'repro'
    app_id = 'repro'
    manual_page = manual_page
    port_forwarding_info = port_forwarding_info


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'repro', ['setup'])
    helper.call('post', app.enable)
