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
from plinth.modules.config.config import get_domainname

version = 1

managed_services = ['filetea']

managed_packages = ['filetea']

title = _('Volatile File Sharing (FileTea)')

description = [
    _('FileTea is an anonymous, volatile file sharing service.\n'
      'Volatile means the shared file is available only as long '
      'as the sender keeps FileTea open on their browser.'),
    format_lazy(
        _('Running FileTea on {box_name} allows you to share files securely '
          'with other users of {box_name}. On a public FileTea service, '
          'anyone with the link can download a shared file. But FileTea on '
          '{box_name} is password protected, so only registered users of '
          '{box_name} can download shared files, not any snooping third '
          'party.'),
        box_name=_(cfg.box_name)),
    _('When enabled, FileTea\'s web interface will be available from '
      '<a href=\"https://{}:8686\">filetea</a>.'.format(get_domainname())),
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
            ports=['filetea-plinth'],
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
    helper.call('configuration', actions.superuser_run, 'filetea',
                ['configure'])
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
        'filetea', title,
        url='https://{}:8686'.format(get_domainname()),
        login_required=True)


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

    results.append(
        action_utils.diagnose_url(
            'http://localhost:8686', kind='4', check_certificate=False))
    results.append(
        action_utils.diagnose_url(
            'http://localhost:8686', kind='6', check_certificate=False))
    results.append(
        action_utils.diagnose_url(
            'https://{}:8686'.format(get_domainname()),
            kind='4',
            check_certificate=False))

    return results
