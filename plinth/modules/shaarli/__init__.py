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
Plinth module to configure Shaarli.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu


version = 1

managed_packages = ['shaarli']

title = _('Bookmarks \n (Shaarli)')

description = [
    _('Shaarli allows you to save and share bookmarks.'),

    _('When enabled, Shaarli will be available from <a href="/shaarli">'
      '/shaarli</a> path on the web server. Note that Shaarli only supports a '
      'single user account, which you will need to setup on the initial '
      'visit.'),
]

service = None


def init():
    """Initialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-bookmark', 'shaarli:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'shaarli', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            'shaarli', title, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('shaarli', title, url='/shaarli',
                           login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('shaarli')


def enable():
    """Enable the module."""
    actions.superuser_run('shaarli', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('shaarli', ['disable'])
    frontpage.remove_shortcut('shaarli')
