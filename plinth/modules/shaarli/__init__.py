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
FreedomBox app to configure Shaarli.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, frontpage
from plinth.menu import main_menu

from .manifest import clients

version = 1

managed_packages = ['shaarli']

name = _('Shaarli')

short_description = _('Bookmarks')

description = [
    _('Shaarli allows you to save and share bookmarks.'),
    _('When enabled, Shaarli will be available from <a href="/shaarli">'
      '/shaarli</a> path on the web server. Note that Shaarli only supports a '
      'single user account, which you will need to setup on the initial '
      'visit.'),
]

clients = clients

service = None

manual_page = 'Shaarli'


def init():
    """Initialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'fa-bookmark', 'shaarli:index',
                     short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'shaarli', name, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

        if is_enabled():
            add_shortcut()
            menu.promote_item('shaarli:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            'shaarli', name, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)
    menu = main_menu.get('apps')
    helper.call('post', menu.promote_item, 'shaarli:index')


def add_shortcut():
    frontpage.add_shortcut('shaarli', name,
                           short_description=short_description, url='/shaarli',
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('shaarli')


def enable():
    """Enable the module."""
    actions.superuser_run('shaarli', ['enable'])
    add_shortcut()
    menu = main_menu.get('apps')
    menu.promote_item('shaarli:index')


def disable():
    """Enable the module."""
    actions.superuser_run('shaarli', ['disable'])
    frontpage.remove_shortcut('shaarli')
    menu = main_menu.get('apps')
    menu.demote_item('shaarli:index')
