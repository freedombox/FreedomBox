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

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy
from plinth.views import ServiceView
from plinth.client import mobile_client, desktop_client

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

desktop_clients = [
    desktop_client(name='Quassel', url='http://quassel-irc.org/downloads')]

mobile_clients = [
    mobile_client(name='QuasselDroid',
                  fully_qualified_name='com.iskrembilen.quasseldroid',
                  fdroid_url=None,
                  play_store_url='https://play.google.com/store/apps/details?'
                                 'id=com.iskrembilen.quasseldroid')]

reserved_usernames = ['quasselcore']


def init():
    """Initialize the quassel module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-retweet', 'quassel:index', short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], name, ports=['quassel-plinth'],
            is_external=True, enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()


class QuasselServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = "quassel"
    description = description


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], name, ports=['quassel-plinth'],
            is_external=True, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('quassel', name,
                           short_description=short_description,
                           details=description,
                           configure_url=reverse_lazy('quassel:index'),
                           login_required=True)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('quassel')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(4242, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(4242, 'tcp6'))

    return results
