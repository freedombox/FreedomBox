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
Plinth module to configure FileTea.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy


version = 1

managed_services = ['filetea']

managed_packages = ['filetea']

title = _('File Sharing \n (FileTea)')

description = [
    _('FileTea is an anonymous, volatile file sharing solution. '
      'It is designed to be simple and easy to use, to run in (modern) browsers without additional plugins, and to avoid the hassle of user registration.'),
    format_lazy(
        _('Running FileTea on {box_name} allows you to share files securely'
           'with other users on the same FreedomBox'), box_name=_(cfg.box_name)),
    _('When enabled, FileTea\'s web interface will be available from '
      '<a href="/filetea/">/filetea</a>.'),
]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-share', 'filetea:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('configuration', actions.superuser_run,
                'filetea', ['configure'])
    action_utils.service_restart('filetea')
    helper.call('post', actions.superuser_run, 'filetea', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut(
        'filetea', title, url='/filetea/', login_required=True)


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('filetea')


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled('filetea') and
            action_utils.webserver_is_enabled('filetea-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('filetea', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('filetea', ['disable'])
    frontpage.remove_shortcut('filetea')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all(
            'https://{host}/filetea/', check_certificate=False))

    return results
