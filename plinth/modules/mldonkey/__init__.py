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
FreedomBox app for mldonkey.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, cfg, frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

managed_services = ['mldonkey-server']

managed_packages = ['mldonkey-server']

name = _('MLDonkey')

short_description = _('Peer-to-peer File Sharing')

description = [
    _('MLDonkey is a peer-to-peer file sharing application used to exchange '
      'large files. It can participate in multiple peer-to-peer networks '
      'including eDonkey, Kademlia, Overnet, BitTorrent and DirectConnect.'),
    format_lazy(
        _('On {box_name}, downloaded files can be found in /var/lib/mldonkey/ '
          'directory.'), box_name=cfg.box_name)
]

clients = clients

reserved_usernames = ['mldonkey']

group = ('ed2k', _('Download files using eDonkey applications'))

service = None

manual_page = 'MLDonkey'


def init():
    """Initialize the MLDonkey module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'mldonkey', 'mldonkey:index', short_description)
    register_group(group)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'mldonkey', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'mldonkey', ['enable'])
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut(
        'mldonkey', name, short_description=short_description,
        url='/mldonkey/', login_required=True, allowed_groups=[group[0]])


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('mldonkey-server')


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('mldonkey-server')
            and action_utils.webserver_is_enabled('mldonkey-freedombox'))


def enable():
    """Enable the module."""
    actions.superuser_run('mldonkey', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('mldonkey', ['disable'])
    frontpage.remove_shortcut('mldonkey')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(4080, 'tcp4'))
    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/mldonkey/',
                                         check_certificate=False))

    return results
