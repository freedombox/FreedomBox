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
FreedomBox app for Quassel.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth import service as service_module
from plinth.utils import format_lazy
from plinth.views import ServiceView

from .manifest import backup, clients

version = 1

service = None

managed_services = ['quasselcore']

managed_packages = ['quassel-core']

name = _('Quassel')

short_description = _('IRC Client')

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
      'are available.'),
]

clients = clients

reserved_usernames = ['quasselcore']

manual_page = 'Quassel'

port_forwarding_info = [('TCP', 4242)]

app = None


class QuasselApp(app_module.App):
    """FreedomBox app for Quassel."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-quassel', name, short_description,
                              'quassel', 'quassel:index',
                              parent_url_name='apps')
        self.add(menu_item)


def init():
    """Initialize the quassel module."""
    global app
    app = QuasselApp()

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'quassel-plinth'
        ], is_external=True, enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()
            app.set_enabled(True)


class QuasselServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "quassel"
    description = description
    clients = clients
    manual_page = manual_page
    port_forwarding_info = port_forwarding_info


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'quassel-plinth'
        ], is_external=True, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)
    helper.call('post', app.enable)


def add_shortcut():
    frontpage.add_shortcut(
        'quassel', name, short_description=short_description,
        details=description, configure_url=reverse_lazy('quassel:index'),
        login_required=True)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()
    app.enable()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('quassel')
    app.disable()


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(4242, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(4242, 'tcp6'))

    return results
